# Ragmine - RAG Plugin for Redmine/RedMica
# Copyright (C) 2024 Your Organization
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

require 'redmine'

# Load plugin libraries
require_dependency File.expand_path('../lib/ragmine/hooks', __FILE__)

Redmine::Plugin.register :ragmine do
  name 'Ragmine - AI Search'
  author 'Your Organization'
  description 'Adds RAG (Retrieval-Augmented Generation) powered search capabilities to Redmine'
  version '0.1.0'
  url 'https://github.com/yourusername/ragmine'
  author_url 'https://yourorganization.com'
  
  # Minimum Redmine version
  requires_redmine version_or_higher: '4.0.0'
  
  # Plugin settings
  settings default: {
    'service_url' => 'http://localhost:8000',
    'api_key' => '',
    'timeout' => 30,
    'enable_cache' => true,
    'cache_ttl' => 300,
    'fallback_mode' => 'basic',
    'max_results' => 20,
    'enable_analytics' => true,
    'index_batch_size' => 100
  }, partial: 'settings/ragmine_settings'
  
  # Define project module
  project_module :ragmine do
    # Permissions for viewing/using RAG search
    permission :use_rag_search, {
      ragmine_search: [:index, :search, :suggestions]
    }, public: false, require: :member
    
    # Permissions for managing RAG settings
    permission :manage_rag_settings, {
      ragmine_admin: [:index, :settings, :reindex, :clear_index]
    }, require: :member
    
    # Permission for viewing analytics
    permission :view_rag_analytics, {
      ragmine_analytics: [:index, :dashboard]
    }, require: :member
  end
  
  # Add menu items
  menu :project_menu, :ragmine_search,
       { controller: 'ragmine_search', action: 'index' },
       caption: :label_ragmine_search,
       after: :issues,
       param: :project_id,
       if: Proc.new { |project| project.enabled_module_names.include?('ragmine') }
  
  menu :admin_menu, :ragmine_settings,
       { controller: 'ragmine_admin', action: 'index' },
       caption: :label_ragmine_admin,
       html: { class: 'icon icon-settings' },
       after: :settings
  
  # Add top menu item for global search (optional)
  menu :top_menu, :ragmine_global_search,
       { controller: 'ragmine_search', action: 'global' },
       caption: :label_ragmine_global_search,
       if: Proc.new { User.current.logged? && Setting.plugin_ragmine['enable_global_search'] }
  
  # Delete menu items if needed
  # delete_menu_item :project_menu, :search
end

# Load patches
Rails.configuration.to_prepare do
  # Patch Issue model to add RAG indexing
  require_dependency 'issue'
  unless Issue.included_modules.include?(Ragmine::Patches::IssuePatch)
    Issue.include(Ragmine::Patches::IssuePatch)
  end
  
  # Patch WikiPage model
  require_dependency 'wiki_page'
  unless WikiPage.included_modules.include?(Ragmine::Patches::WikiPagePatch)
    WikiPage.include(Ragmine::Patches::WikiPagePatch)
  end
  
  # Patch Document model
  require_dependency 'document'
  unless Document.included_modules.include?(Ragmine::Patches::DocumentPatch)
    Document.include(Ragmine::Patches::DocumentPatch)
  end
end
