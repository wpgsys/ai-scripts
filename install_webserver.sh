#!/bin/bash

# -----------------------------------------------------------------------------
# MacOS Apache & PHP 8.2 Setup Script
# -----------------------------------------------------------------------------
# This script is designed for macOS systems with Homebrew installed. It configures
# Apache (httpd) to use PHP 8.2, ensuring that the setup is safe to run multiple
# times without causing configuration issues. The script corrects any duplicate
# or malformed configuration entries and is intended for users who want to run 
# Apache on localhost, listening on port 8080.
# 
# Requirements:
# - macOS with Homebrew installed
# - Apache (httpd) and PHP 8.2 installed via Homebrew
#
# What this script does:
# - Installs and configures PHP 8.2 with Apache if not already installed
# - Ensures Apache is configured to listen on port 8080
# - Fixes any malformed or duplicated configuration settings
# - Safely restarts Apache to apply the changes
# -----------------------------------------------------------------------------

# Ensure Homebrew is installed
if ! command -v brew &> /dev/null
then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew is already installed."
fi

# Update Homebrew
echo "Updating Homebrew..."
brew update

# Install PHP 8.2 if not already installed
if brew ls --versions php@8.2 > /dev/null; then
    echo "PHP 8.2 is already installed."
else
    echo "Installing PHP 8.2..."
    brew install php@8.2
fi

# Link PHP 8.2 to be the default PHP version, only if not already linked
if ! php -v | grep -q "PHP 8.2"; then
    echo "Linking PHP 8.2..."
    brew link --force --overwrite php@8.2
else
    echo "PHP 8.2 is already linked."
fi

# Install Apache (httpd) if not already installed
if brew ls --versions httpd > /dev/null; then
    echo "Apache (httpd) is already installed."
else
    echo "Installing Apache (httpd)..."
    brew install httpd
fi

# Configure Apache to use PHP
echo "Configuring Apache to use PHP 8.2..."

# Correct path for Homebrew installed Apache
APACHE_CONF="/opt/homebrew/etc/httpd/httpd.conf"

# Preset configuration blocks
PHP_MODULE_CONFIG="LoadModule php_module /opt/homebrew/opt/php@8.2/lib/httpd/modules/libphp.so"
PHP_HANDLER_CONFIG="<FilesMatch \.php$>\n    SetHandler application/x-httpd-php\n</FilesMatch>"

# Remove existing PHP module and handler if found, then add preset
sed -i '' '/LoadModule php_module/d' "$APACHE_CONF"
sed -i '' '/<FilesMatch \\.php$/d' "$APACHE_CONF"
sed -i '' '/SetHandler application\/x-httpd-php/d' "$APACHE_CONF"
echo -e "$PHP_MODULE_CONFIG\n$PHP_HANDLER_CONFIG" >> "$APACHE_CONF"
echo "PHP configuration updated in Apache."

# Ensure Apache is set to listen on the correct port
PORT=8080

# Correct any malformed Listen directives
sed -i '' -E 's/^Listen [0-9]{2,}$//g' "$APACHE_CONF"

# Ensure correct Listen directive is present
if ! grep -q "^Listen $PORT" "$APACHE_CONF"; then
    echo "Listen $PORT" >> "$APACHE_CONF"
    echo "Apache is now set to listen on port $PORT."
fi

# Validate that the Listen directive is set correctly
if ! grep -q "^Listen $PORT" "$APACHE_CONF"; then
    echo "Error: Apache is not correctly configured to listen on port $PORT. Please check your configuration."
    exit 1
fi

# Test the Apache configuration before restarting
echo "Testing Apache configuration..."
apachectl configtest

if [ $? -ne 0 ]; then
    echo "Apache configuration test failed. Aborting script to prevent breaking the server."
    exit 1
fi

# Restart Apache service if necessary
if brew services list | grep -q "httpd.*started"; then
    echo "Restarting Apache service..."
    brew services restart httpd
else
    echo "Starting Apache service..."
    brew services start httpd
fi

# Ensure PHP-FPM is not running (if previously used with Nginx)
if brew services list | grep -q "php@8.2.*started"; then
    echo "Stopping PHP-FPM service..."
    brew services stop php@8.2
else
    echo "PHP-FPM service is not running."
fi

echo "Setup complete! Apache with PHP 8.2 is now running on http://localhost:$PORT"

# Optional: Open a webpage to verify the installation
echo "You can verify your setup by creating a PHP info page in your web root."
echo "Example: echo '<?php phpinfo(); ?>' > /opt/homebrew/var/www/index.php"
echo "Visit http://localhost:$PORT to verify that your server is working."
