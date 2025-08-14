# Ragmine Plugin Routes

# Project-specific routes
resources :projects do
  resources :ragmine_search, only: [:index] do
    collection do
      get :search
      get :suggestions
      post :feedback
    end
  end
  
  namespace :ragmine do
    resources :analytics, only: [:index] do
      collection do
        get :dashboard
        get :queries
        get :performance
      end
    end
  end
end

# Global search route (no project context)
get 'ragmine/search', to: 'ragmine_search#global', as: :ragmine_global_search
get 'ragmine/suggestions', to: 'ragmine_search#global_suggestions'

# Admin routes
namespace :admin do
  resources :ragmine_settings, only: [:index] do
    collection do
      post :test_connection
      post :reindex
      post :clear_index
      get :indexing_status
      patch :update_settings
    end
  end
end

# API routes for external service callbacks
namespace :api do
  namespace :ragmine do
    post 'callback/:document_id', to: 'callbacks#document_indexed'
    post 'webhook/index_complete', to: 'webhooks#index_complete'
  end
end
