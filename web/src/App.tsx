import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { Header } from '@/components/layout'
import { MemorySidebar, MemoryList, MemoryDetail, MemoryEditor } from '@/components/memory'
import { ChatSidebar, ChatPanel } from '@/components/chat'
import { BackendSidebar, BackendDetail, ConnectModal } from '@/components/backend'
import { Button } from '@/components/ui'
import { useAppStore, useMemoryStore, useBackendStore } from '@/stores'
import { useState } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

function App() {
  const { mode } = useAppStore()
  const { selectedMemoryId, setSelectedMemoryId } = useMemoryStore()
  const { selectedProvider, isConnectModalOpen, setIsConnectModalOpen } = useBackendStore()
  const [isMemoryEditorOpen, setIsMemoryEditorOpen] = useState(false)

  const renderContent = () => {
    switch (mode) {
      case 'memory':
        return (
          <div className="flex flex-1 overflow-hidden">
            <MemorySidebar />
            <MemoryList onMemoryClick={setSelectedMemoryId} />
            {selectedMemoryId && (
              <MemoryDetail
                memoryId={selectedMemoryId}
                onClose={() => setSelectedMemoryId(null)}
              />
            )}
          </div>
        )

      case 'chat':
        return (
          <div className="flex flex-1 overflow-hidden">
            <ChatSidebar />
            <ChatPanel />
          </div>
        )

      case 'backend':
        return (
          <div className="flex flex-1 overflow-hidden">
            <BackendSidebar />
            {selectedProvider ? (
              <BackendDetail provider={selectedProvider} />
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">🗄️</span>
                  </div>
                  <p className="text-text-muted">选择或添加后端</p>
                </div>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background flex flex-col">
        <Header />

        {/* FAB for Memory Mode */}
        {mode === 'memory' && (
          <Button
            className="fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-lg text-xl"
            onClick={() => setIsMemoryEditorOpen(true)}
          >
            +
          </Button>
        )}

        <main className="flex-1 flex overflow-hidden">
          {renderContent()}
        </main>

        {/* Modals */}
        <MemoryEditor
          isOpen={isMemoryEditorOpen}
          onClose={() => setIsMemoryEditorOpen(false)}
        />
        <ConnectModal
          isOpen={isConnectModalOpen}
          onClose={() => setIsConnectModalOpen(false)}
        />
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#faf9f7',
            color: '#374151',
            border: '1px solid #e5e7eb',
          },
        }}
      />
    </QueryClientProvider>
  )
}

export default App
