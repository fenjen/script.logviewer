# Command Viewer for Kodi

## Examples

```bash
docker logs -f container
tail -f /var/log/syslog | grep problems
```

**Default**
```bash
tail -f kodi.log
```

## Settings

- Follow Docker logs
  - Lines: 42
  - Font: small font
  - Update interval: 100 ms

- Read kodi.log
  - Command: (leave empty)
  - Lines: 500
  - Update interval: 60000 ms (new content resets scrolling)

- Follow kodi.log
  - Command: (leave empty)
  - Lines: 42
  - Font: small font
  - Update interval: 1000 ms
