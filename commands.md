  # Count how many videos have been completed
  find USER-FILES/05.OUTPUT/ -name "*.mp4" 2>/dev/null | wc -l

   # See what's being created right now
  watch -n 2 'ls -la USER-FILES/05.OUTPUT/ | tail -5'