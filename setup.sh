#!/bin/bash
# Ragmine Plugin Setup Script
# This script initializes the Ragmine plugin structure

echo "🚀 Setting up Ragmine plugin structure..."

# Create main plugin directories
mkdir -p app/{controllers,models,views,jobs,helpers}
mkdir -p app/views/{ragmine_search,ragmine_admin,settings}
mkdir -p assets/{stylesheets,javascripts,images}
mkdir -p config/locales
mkdir -p db/migrate
mkdir -p lib/ragmine/{patches,search}
mkdir -p lib/tasks
mkdir -p test/{unit,functional,integration,fixtures}

# Create RAG service directories
mkdir -p rag_service/{api,pipeline,transformers,routing,models,tests}

# Create Docker and deployment directories
mkdir -p docker
mkdir -p k8s
mkdir -p docs

echo "📁 Directory structure created"

# Create initial files
touch init.rb
touch Gemfile
touch README.md
touch LICENSE
touch .gitignore
touch .rubocop.yml

# Create config files
touch config/routes.rb
touch config/settings.yml
touch config/locales/en.yml

# Create test helper
touch test/test_helper.rb

# Create RAG service files
touch rag_service/app.py
touch rag_service/config.py
touch rag_service/requirements.txt
touch rag_service/Dockerfile
touch rag_service/.env.example

# Create Docker files
touch docker-compose.yml
touch Dockerfile

# Create documentation files
touch docs/installation.md
touch docs/configuration.md
touch docs/api.md
touch docs/troubleshooting.md

echo "📄 Initial files created"

# Make script executable
chmod +x setup.sh

echo "✅ Ragmine plugin structure initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Run 'bundle exec rails generate redmine_plugin Ragmine' from your Redmine root"
echo "2. Copy this structure to plugins/ragmine in your Redmine installation"
echo "3. Run 'bundle install' to install dependencies"
echo "4. Run 'bundle exec rake redmine:plugins:migrate' to setup database"
