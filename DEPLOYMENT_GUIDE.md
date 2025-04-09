# HackBlockNexus Deployment Guide

This guide will help you deploy the HackBlockNexus website with MySQL database and email verification.

## Prerequisites

- A web hosting provider that supports Python and MySQL
- A domain name (optional but recommended)
- An email account for sending verification emails

## Step 1: Set Up MySQL Database

1. Create a MySQL database on your hosting provider
2. Note down the following information:
   - Database hostname
   - Database name
   - Database username
   - Database password
   - Database port (usually 3306)

## Step 2: Configure Environment Variables

Update the `.env` file with your actual values:

```
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key-change-this

# MySQL Database Configuration
MYSQL_HOST=your-mysql-host
MYSQL_USER=your-mysql-username
MYSQL_PASSWORD=your-mysql-password
MYSQL_DB=your-mysql-database-name
MYSQL_PORT=3306

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Security Settings
SECURITY_PASSWORD_SALT=your-password-salt-for-tokens
```

Notes:
- For Gmail, you'll need to create an "App Password" in your Google account security settings
- Generate secure random strings for SECRET_KEY and SECURITY_PASSWORD_SALT

## Step 3: Deploy the Application

### Option 1: Deploy to a PaaS (Platform as a Service) like Heroku

1. Create an account on Heroku or similar platform
2. Install the Heroku CLI and login
3. Initialize a git repository in your project folder:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
4. Create a new Heroku app:
   ```
   heroku create hackblocknexus
   ```
5. Add a Procfile for Heroku:
   ```
   web: gunicorn app:app
   ```
6. Set up environment variables on Heroku:
   ```
   heroku config:set FLASK_APP=app.py
   heroku config:set FLASK_ENV=production
   # Add all other environment variables from your .env file
   ```
7. Add a MySQL add-on:
   ```
   heroku addons:create jawsdb
   ```
8. Push your code to Heroku:
   ```
   git push heroku master
   ```
9. Initialize the database:
   ```
   heroku run python init_db.py
   ```

### Option 2: Deploy to a VPS (Virtual Private Server)

1. Connect to your VPS via SSH
2. Install required packages:
   ```
   sudo apt-get update
   sudo apt-get install python3-pip python3-dev mysql-server nginx
   ```
3. Clone your repository:
   ```
   git clone <your-repository-url>
   cd hackblocknexus
   ```
4. Create a virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Set up MySQL:
   ```
   sudo mysql
   CREATE DATABASE hackblocknexus;
   CREATE USER 'hackblocknexus'@'localhost' IDENTIFIED BY 'your-password';
   GRANT ALL PRIVILEGES ON hackblocknexus.* TO 'hackblocknexus'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```
6. Update your .env file with the MySQL credentials
7. Initialize the database:
   ```
   python init_db.py
   ```
8. Set up Gunicorn:
   ```
   sudo nano /etc/systemd/system/hackblocknexus.service
   ```
   Add the following:
   ```
   [Unit]
   Description=Gunicorn instance to serve HackBlockNexus
   After=network.target

   [Service]
   User=<your-username>
   Group=www-data
   WorkingDirectory=/path/to/hackblocknexus
   Environment="PATH=/path/to/hackblocknexus/venv/bin"
   ExecStart=/path/to/hackblocknexus/venv/bin/gunicorn --workers 3 --bind unix:hackblocknexus.sock -m 007 app:app

   [Install]
   WantedBy=multi-user.target
   ```
9. Start and enable the service:
   ```
   sudo systemctl start hackblocknexus
   sudo systemctl enable hackblocknexus
   ```
10. Configure Nginx:
    ```
    sudo nano /etc/nginx/sites-available/hackblocknexus
    ```
    Add the following:
    ```
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;

        location / {
            include proxy_params;
            proxy_pass http://unix:/path/to/hackblocknexus/hackblocknexus.sock;
        }
    }
    ```
11. Enable the site and restart Nginx:
    ```
    sudo ln -s /etc/nginx/sites-available/hackblocknexus /etc/nginx/sites-enabled
    sudo systemctl restart nginx
    ```

## Step 4: Test Your Deployment

1. Visit your website URL
2. Test user registration and email verification
3. Verify that all features are working correctly

## Troubleshooting

### Email Verification Issues
- Check your SMTP settings in the .env file
- Ensure your email provider allows SMTP access
- For Gmail, use an App Password instead of your regular password

### Database Connection Issues
- Verify your MySQL credentials
- Check if the MySQL server is running
- Ensure your hosting provider allows external MySQL connections

### Application Errors
- Check the application logs:
  - On Heroku: `heroku logs --tail`
  - On VPS: `sudo journalctl -u hackblocknexus.service`

## Security Considerations

1. Always use HTTPS in production
2. Keep your .env file secure and never commit it to public repositories
3. Regularly update dependencies to patch security vulnerabilities
4. Consider implementing rate limiting for login attempts
5. Set up regular database backups

For any further assistance, please refer to the Flask and MySQL documentation.
