# **AI Chat Interface - Implementation Specification**

This specification outlines a **modern AI chat interface** built with shadcn/ui components, focusing on core chat functionality and file integration.

## **Core Chat Interface Architecture**

### **Main Layout Structure**

**Primary Components:**
- **Chat Header**: Context tabs and user actions
- **Message Area**: Scrollable conversation history
- **Input Area**: Text input with file attachment support
- **Sidebar**: Conversation history and quick actions

**Layout Structure:**
```
Chat Interface
├── Header
│   ├── Context Tabs (Q&A, Docs, RFP)
│   └── User Profile & Actions
├── Main Content
│   ├── Message History
│   ├── Suggested Prompts
│   └── Input Area
└── Sidebar
    ├── Recent Conversations
    └── Quick Actions
```

### **Key Interface Elements**

**Chat Header:**
- **Context Tabs**: Q&A (active), Docs (disabled), RFP (disabled)
- **User Avatar**: Profile access and settings
- **File Upload Button**: Quick access to file upload

**Message Area:**
- **Conversation History**: Scrollable message list with timestamps
- **Message Types**: User messages, AI responses, system messages
- **File Attachments**: Inline display of uploaded files
- **Suggested Prompts**: 2x2 grid of conversation starters

## **Component Implementation**

### **Chat Header Component**
```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

export function ChatHeader() {
  return (
    <div className="flex items-center justify-between p-4 border-b">
      <Tabs defaultValue="qa" className="w-full">
        <TabsList>
          <TabsTrigger value="qa">Q&A</TabsTrigger>
          <TabsTrigger value="docs" disabled>Docs</TabsTrigger>
          <TabsTrigger value="rfp" disabled>RFP</TabsTrigger>
        </TabsList>
      </Tabs>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          Upload Files
        </Button>
        <Avatar>
          <AvatarImage src="/user-avatar.jpg" />
          <AvatarFallback>U</AvatarFallback>
        </Avatar>
      </div>
    </div>
  )
}
```

### **Message Area Component**
```tsx
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent } from "@/components/ui/card"

export function MessageArea() {
  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4">
        {/* Message components */}
        <div className="flex justify-end">
          <Card className="max-w-[80%]">
            <CardContent className="p-3">
              <p>User message content</p>
            </CardContent>
          </Card>
        </div>
        <div className="flex justify-start">
          <Card className="max-w-[80%]">
            <CardContent className="p-3">
              <p>AI response content</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </ScrollArea>
  )
}
```

### **Input Area Component**
```tsx
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Paperclip, Send } from "lucide-react"

export function InputArea() {
  return (
    <div className="p-4 border-t">
      <div className="flex gap-2">
        <Button variant="outline" size="icon">
          <Paperclip className="h-4 w-4" />
        </Button>
        <Textarea 
          placeholder="Type your message... (⌘+Enter to send)"
          className="flex-1 min-h-[60px]"
        />
        <Button size="icon">
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
```

### **Suggested Prompts Component**
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function SuggestedPrompts() {
  const prompts = [
    "Analyze the uploaded document",
    "Summarize key findings",
    "Create a proposal outline",
    "Generate questions for review"
  ]

  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      {prompts.map((prompt, index) => (
        <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow">
          <CardContent className="p-4">
            <p className="text-sm text-muted-foreground">{prompt}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
```

## **File Integration Features**

### **File Upload Integration**
- **Drag & Drop**: Support for dragging files directly into chat
- **File Attachments**: Inline display of uploaded files in messages
- **File Types**: Support for PDF, DOC, DOCX, TXT, images
- **File Preview**: Quick preview of attached files

### **State Management**
```tsx
interface ChatState {
  messages: Message[]
  activeTab: 'qa' | 'docs' | 'rfp'
  attachedFiles: File[]
  isLoading: boolean
}

interface Message {
  id: string
  type: 'user' | 'ai' | 'system'
  content: string
  timestamp: Date
  attachments?: File[]
}
```

## **Implementation Priority**

1. **Core Chat Interface**: Basic message display and input
2. **File Upload**: Drag & drop and attachment support
3. **Context Tabs**: Q&A, Docs, RFP functionality
4. **Suggested Prompts**: Conversation starters
5. **Advanced Features**: Search, history, keyboard shortcuts

This specification provides a **focused implementation roadmap** for building a modern AI chat interface with shadcn/ui components, prioritizing core chat functionality and file integration.

