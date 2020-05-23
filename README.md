# Snahp Cron

### Edit crontab
sudo vi /etc/crontab
Add the following entry:
```
*/10 * * * * [username] python /path/to/cron.py
```
Replace [username] with appropriate username.
