require 'ragmine_core'

Redmine::Plugin.register :ragmine_core do
  name 'RAGMine Core'
  author 'RAGMine Team'
  description 'Core functionality for RAGMine - vector embeddings and content indexing'
  version '0.1.0'
  url 'https://github.com/zacharyelston/ragmine'
  
  # Minimum Redmine version
  requires_redmine version_or_higher: '4.2.0'
  
  # Permissions for managing RAG features
  permission :manage_rag_embeddings, {}, require: :member
  permission :view_rag_content, {}, public: true
  
  # Add menu items if needed
  menu :admin_menu, :ragmine_settings, 
       { controller: 'ragmine_admin', action: 'index' },
       caption: 'RAGMine Settings',
       if: Proc.new { User.current.admin? }
end

# Register hooks for content changes
require 'ragmine_core/hooks'