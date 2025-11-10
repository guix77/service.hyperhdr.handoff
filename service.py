"""
Kodi service addon for HyperHDR handoff control.

This service automatically manages HyperHDR LEDDEVICE component state:
- On startup: Forces ALL=false (with retries)
- On video playback start: Sets ALL=true
- On video playback stop/end: Sets ALL=false
"""

import json
import time
import urllib.request
from datetime import datetime
import xbmc
import xbmcaddon

# Addon instance for settings
ADDON = xbmcaddon.Addon()

# Default values (used as fallback if settings are not available)
DEFAULT_HYPERHDR_URL = "http://127.0.0.1:8090/json-rpc"
DEFAULT_STARTUP_DELAY = 5.0
DEFAULT_RETRIES = 5
DEFAULT_RETRY_SLEEP = 0.8
DEFAULT_REQ_TIMEOUT = 2


def get_setting(setting_id, default_value):
    """
    Get addon setting value with fallback to default.
    
    Args:
        setting_id (str): Setting ID from settings.xml
        default_value: Default value if setting is not available
        
    Returns:
        Setting value or default
    """
    try:
        value = ADDON.getSetting(setting_id)
        if value is None or value == "":
            return default_value
        # Convert to appropriate type based on default
        if isinstance(default_value, bool):
            # Kodi returns "true"/"false" as strings, handle various formats
            return str(value).lower() in ("true", "1", "yes")
        elif isinstance(default_value, float):
            return float(value)
        elif isinstance(default_value, int):
            return int(value)
        return value
    except Exception:
        return default_value


def post_json(payload, hyperhdr_url, retries, retry_sleep, req_timeout):
    """
    Send JSON-RPC POST request to HyperHDR.
    
    Args:
        payload (dict): JSON-RPC payload
        hyperhdr_url (str): HyperHDR JSON-RPC endpoint URL
        retries (int): Number of retry attempts
        retry_sleep (float): Sleep time between retries in seconds
        req_timeout (float): Request timeout in seconds
        
    Returns:
        bool: True if request succeeded, False otherwise
    """
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        hyperhdr_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=req_timeout) as resp:
                resp.read()
            if attempt > 0:
                xbmc.log("[HyperHDR Handoff] Request succeeded after %d retries" % attempt, xbmc.LOGINFO)
            return True
        except urllib.error.URLError as e:
            xbmc.log("[HyperHDR Handoff] HTTP error (attempt %d/%d): %s" % (attempt + 1, retries, e), xbmc.LOGWARNING)
            if attempt < retries - 1:
                time.sleep(retry_sleep)
        except Exception as e:
            xbmc.log("[HyperHDR Handoff] Unexpected error (attempt %d/%d): %s" % (attempt + 1, retries, e), xbmc.LOGWARNING)
            if attempt < retries - 1:
                time.sleep(retry_sleep)
    
    xbmc.log("[HyperHDR Handoff] Failed to connect to HyperHDR after %d attempts" % retries, xbmc.LOGERROR)
    return False


def is_time_in_range(time_start, time_end):
    """
    Check if current local time is within the specified time range.
    Handles ranges that cross midnight (e.g., 22:00-06:00).
    
    Args:
        time_start (str): Start time in HH:MM format
        time_end (str): End time in HH:MM format
        
    Returns:
        bool: True if current time is within range, False otherwise
    """
    try:
        now = datetime.now()
        current_time = now.hour * 60 + now.minute
        current_str = "%02d:%02d" % (now.hour, now.minute)
        
        # Parse start and end times
        start_hour, start_min = map(int, time_start.split(":"))
        end_hour, end_min = map(int, time_end.split(":"))
        start_time = start_hour * 60 + start_min
        end_time = end_hour * 60 + end_min
        
        # Handle range that crosses midnight
        if start_time > end_time:
            # Range crosses midnight (e.g., 22:00-06:00)
            in_range = current_time >= start_time or current_time < end_time
        else:
            # Normal range within same day (e.g., 09:00-17:00)
            in_range = start_time <= current_time < end_time
        
        xbmc.log("[HyperHDR Handoff] Time check: current=%s, range=%s-%s, in_range=%s" % 
                (current_str, time_start, time_end, in_range), xbmc.LOGDEBUG)
        return in_range
    except Exception as e:
        xbmc.log("[HyperHDR Handoff] Error parsing time range: %s" % e, xbmc.LOGERROR)
        return False


def set_all(state, hyperhdr_url, retries, retry_sleep, req_timeout):
    """
    Set HyperHDR LEDDEVICE component state.
    
    Args:
        state (bool): True to enable, False to disable
        hyperhdr_url (str): HyperHDR JSON-RPC endpoint URL
        retries (int): Number of retry attempts
        retry_sleep (float): Sleep time between retries in seconds
        req_timeout (float): Request timeout in seconds
        
    Returns:
        bool: True if request succeeded, False otherwise
    """
    return post_json(
        {
            "command": "componentstate",
            "componentstate": {"component": "ALL", "state": bool(state)}
        },
        hyperhdr_url,
        retries,
        retry_sleep,
        req_timeout
    )


class HandoffPlayer(xbmc.Player):
    """Kodi player monitor for HyperHDR handoff control."""
    
    def __init__(self):
        """Initialize player with addon settings."""
        super(HandoffPlayer, self).__init__()
        self.hyperhdr_url = get_setting("hyperhdr_url", DEFAULT_HYPERHDR_URL)
        self.retries = get_setting("retry_count", DEFAULT_RETRIES)
        self.retry_sleep = get_setting("retry_sleep", DEFAULT_RETRY_SLEEP)
        self.req_timeout = get_setting("request_timeout", DEFAULT_REQ_TIMEOUT)
    
    def _get_time_settings(self):
        """Get time-related settings (reloaded each time to pick up changes)."""
        return {
            "enabled": get_setting("time_enabled", False),
            "start": get_setting("time_start", "20:00"),
            "end": get_setting("time_end", "06:00")
        }
    
    def onAVStarted(self):
        """Called when audio/video playback starts."""
        try:
            if self.isPlayingVideo():
                time_settings = self._get_time_settings()
                # Check if time range is enabled and if current time is in range
                if time_settings["enabled"]:
                    if is_time_in_range(time_settings["start"], time_settings["end"]):
                        xbmc.log("[HyperHDR Handoff] Video started -> ALL=true (time in range %s-%s)" % 
                                (time_settings["start"], time_settings["end"]), xbmc.LOGINFO)
                        set_all(True, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
                    else:
                        xbmc.log("[HyperHDR Handoff] Video started but time outside range (%s-%s) -> skipping activation" % 
                                (time_settings["start"], time_settings["end"]), xbmc.LOGINFO)
                else:
                    # Time check disabled, use normal behavior
                    xbmc.log("[HyperHDR Handoff] Video started -> ALL=true", xbmc.LOGINFO)
                    set_all(True, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
        except Exception as e:
            xbmc.log("[HyperHDR Handoff] onAVStarted error: %s" % e, xbmc.LOGERROR)
    
    def onPlayBackStopped(self):
        """Called when playback is stopped by user."""
        try:
            time_settings = self._get_time_settings()
            # Check if time range is enabled and if current time is in range
            if time_settings["enabled"]:
                if is_time_in_range(time_settings["start"], time_settings["end"]):
                    xbmc.log("[HyperHDR Handoff] Playback stopped -> ALL=false (time in range)", xbmc.LOGINFO)
                    set_all(False, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
                else:
                    xbmc.log("[HyperHDR Handoff] Playback stopped but time outside range (%s-%s) -> skipping deactivation" % 
                            (time_settings["start"], time_settings["end"]), xbmc.LOGINFO)
            else:
                # Time check disabled, use normal behavior
                xbmc.log("[HyperHDR Handoff] Playback stopped -> ALL=false", xbmc.LOGINFO)
                set_all(False, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
        except Exception as e:
            xbmc.log("[HyperHDR Handoff] onPlayBackStopped error: %s" % e, xbmc.LOGERROR)
    
    def onPlayBackEnded(self):
        """Called when playback ends naturally."""
        try:
            time_settings = self._get_time_settings()
            # Check if time range is enabled and if current time is in range
            if time_settings["enabled"]:
                if is_time_in_range(time_settings["start"], time_settings["end"]):
                    xbmc.log("[HyperHDR Handoff] Playback ended -> ALL=false (time in range)", xbmc.LOGINFO)
                    set_all(False, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
                else:
                    xbmc.log("[HyperHDR Handoff] Playback ended but time outside range (%s-%s) -> skipping deactivation" % 
                            (time_settings["start"], time_settings["end"]), xbmc.LOGINFO)
            else:
                # Time check disabled, use normal behavior
                xbmc.log("[HyperHDR Handoff] Playback ended -> ALL=false", xbmc.LOGINFO)
                set_all(False, self.hyperhdr_url, self.retries, self.retry_sleep, self.req_timeout)
        except Exception as e:
            xbmc.log("[HyperHDR Handoff] onPlayBackEnded error: %s" % e, xbmc.LOGERROR)


if __name__ == "__main__":
    xbmc.log("[HyperHDR Handoff] Service starting...", xbmc.LOGINFO)
    
    # Load settings
    hyperhdr_url = get_setting("hyperhdr_url", DEFAULT_HYPERHDR_URL)
    startup_delay = get_setting("startup_delay", DEFAULT_STARTUP_DELAY)
    retries = get_setting("retry_count", DEFAULT_RETRIES)
    retry_sleep = get_setting("retry_sleep", DEFAULT_RETRY_SLEEP)
    req_timeout = get_setting("request_timeout", DEFAULT_REQ_TIMEOUT)
    
    xbmc.log("[HyperHDR Handoff] Configuration: URL=%s, Delay=%.1fs, Retries=%d" % 
             (hyperhdr_url, startup_delay, retries), xbmc.LOGINFO)
    
    # Initialize player and monitor
    player = HandoffPlayer()
    monitor = xbmc.Monitor()
    
    # Wait for HyperHDR to be ready, then force OFF state (idempotent)
    time.sleep(startup_delay)
    xbmc.log("[HyperHDR Handoff] Startup -> force ALL=false", xbmc.LOGINFO)
    set_all(False, hyperhdr_url, retries, retry_sleep, req_timeout)
    
    # Main service loop
    while not monitor.abortRequested():
        monitor.waitForAbort(1.0)
    
    xbmc.log("[HyperHDR Handoff] Service stopping.", xbmc.LOGINFO)
