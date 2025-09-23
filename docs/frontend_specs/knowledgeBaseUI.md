# **Knowledge Sources Management - Implementation Specification**

This specification outlines a **modern file management interface** built with shadcn/ui components, focusing on file upload, organization, and integration capabilities.

## **Core File Management Architecture**

### **Main Layout Structure**

**Primary Components:**
- **File Browser**: Hierarchical file and folder structure
- **Upload Interface**: Drag-and-drop file upload with progress tracking
- **Search & Filter**: Real-time content discovery
- **Integration Cards**: Visual status of connected services

**Layout Structure:**
```
Knowledge Sources
├── Header
│   ├── Page Title
│   ├── Upload Button
│   └── Search Bar
├── Content Tabs
│   ├── Files Tab
│   ├── URLs Tab
│   └── Integrations Tab
├── File Browser
│   ├── Folder Tree
│   ├── File List
│   └── File Details
└── Action Panel
    ├── Upload Zone
    ├── Integration Status
    └── Bulk Actions
```

## **File Upload Implementation**

### **Upload Modal Component**
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export function UploadModal({ open, onOpenChange }: UploadModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Upload Files</DialogTitle>
        </DialogHeader>
        <Tabs defaultValue="files" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="files">Files</TabsTrigger>
            <TabsTrigger value="urls">Web URLs</TabsTrigger>
            <TabsTrigger value="integrations">Integrations</TabsTrigger>
          </TabsList>
          <TabsContent value="files">
      <FileUploadSection />
          </TabsContent>
          <TabsContent value="urls">
      <URLInputSection />
          </TabsContent>
          <TabsContent value="integrations">
      <IntegrationSection />
          </TabsContent>
  </Tabs>
      </DialogContent>
    </Dialog>
  )
}
```

### **File Upload Section Component**
```tsx
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Upload, FileText, Image, File } from "lucide-react"

export function FileUploadSection() {
  return (
    <div className="space-y-4">
      <Card className="border-2 border-dashed border-muted-foreground/25">
        <CardContent className="flex flex-col items-center justify-center p-8">
          <Upload className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">Drag files here to upload</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Supports: PDF, DOC, DOCX, TXT, XLS, PPT, Images
          </p>
          <Button>
            <Upload className="h-4 w-4 mr-2" />
      Choose Files
    </Button>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-3 gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FileText className="h-4 w-4" />
          Documents
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Image className="h-4 w-4" />
          Images
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <File className="h-4 w-4" />
          Other Files
        </div>
      </div>
  </div>
  )
}
```

### **Supported File Types**
- **Documents**: PDF, DOC, DOCX, TXT
- **Spreadsheets**: XLS, XLSX, CSV
- **Presentations**: PPT, PPTX
- **Images**: JPG, PNG, GIF, SVG
- **Other**: JSON, XML, MD

### **Upload Features**
- **Drag & Drop**: Direct file dropping into upload area
- **Multiple Selection**: Batch upload capability
- **Progress Tracking**: Real-time upload progress
- **File Validation**: Size and type restrictions
- **Error Handling**: Upload failure recovery

### **URL Input Section Component**
```tsx
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Globe } from "lucide-react"

export function URLInputSection() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Add Web URL</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="url">Website URL</Label>
            <div className="relative">
              <Globe className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
    <Input
                id="url"
                placeholder="https://example.com/document.pdf"
                className="pl-10"
              />
            </div>
          </div>
          <Button className="w-full">
      Add URL
    </Button>
        </CardContent>
      </Card>
      
      <div className="text-sm text-muted-foreground">
        <p>Supported formats:</p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li>Web pages and articles</li>
          <li>PDF documents</li>
          <li>Documentation sites</li>
          <li>Knowledge bases</li>
        </ul>
      </div>
    </div>
  )
}
```

### **URL Processing Features**
- **URL Validation**: Comprehensive validation for proper URL format
- **Protocol Support**: HTTP and HTTPS protocol validation
- **Content Extraction**: Automatic content fetching and indexing
- **Preview Generation**: URL preview with metadata extraction
- **Duplicate Detection**: Prevention of duplicate URL entries

### **Integration Section Component**
```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Cloud, Database, FileText } from "lucide-react"

export function IntegrationSection() {
  const integrations = [
    {
      name: "Google Drive",
      description: "Connect your Google Drive account",
      icon: Cloud,
      status: "connected",
      connected: true
    },
    {
      name: "Microsoft OneDrive",
      description: "Sync with OneDrive files",
      icon: Cloud,
      status: "available",
      connected: false
    },
    {
      name: "Notion",
      description: "Import from Notion workspace",
      icon: Database,
      status: "available",
      connected: false
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {integrations.map((integration) => (
        <Card key={integration.name} className="cursor-pointer hover:shadow-md transition-shadow">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <integration.icon className="h-6 w-6 text-muted-foreground" />
                <div>
                  <CardTitle className="text-base">{integration.name}</CardTitle>
                </div>
              </div>
              <Badge variant={integration.connected ? "default" : "secondary"}>
                {integration.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <p className="text-sm text-muted-foreground mb-3">
              {integration.description}
            </p>
            <Button 
              variant={integration.connected ? "outline" : "default"}
              size="sm"
              className="w-full"
            >
              {integration.connected ? "Manage" : "Connect"}
            </Button>
          </CardContent>
    </Card>
      ))}
    </div>
  )
}
```

### **Available Integrations**
- **Google Drive**: Primary cloud storage integration
- **Microsoft OneDrive**: Enterprise cloud storage option
- **Dropbox**: Alternative cloud storage solution
- **Notion**: Knowledge base integration
- **Confluence**: Atlassian wiki integration
- **SharePoint**: Microsoft enterprise document management

### **Integration Features**
- **OAuth Authentication**: Secure connection establishment
- **Permission Scopes**: Read-only or read-write access levels
- **Sync Status Indicators**: Connection health and sync status
- **Folder Selection**: Choose specific folders for synchronization
- **Auto-sync Configuration**: Scheduled synchronization settings

## **State Management**

### **File Management State**
```typescript
interface FileManagementState {
  files: {
    uploading: File[]
    completed: FileRecord[]
    failed: File[]
  }
  urls: {
    processing: string[]
    completed: URLRecord[]
    failed: string[]
  }
  integrations: {
    connected: Integration[]
    syncing: Integration[]
    errors: IntegrationError[]
  }
  modal: {
    visible: boolean
    activeTab: 'files' | 'urls' | 'integrations'
  }
}

interface FileRecord {
  id: string
  name: string
  type: string
  size: number
  uploadedAt: Date
  status: 'processing' | 'completed' | 'failed'
}
```

## **Implementation Priority**

1. **File Upload Modal**: Basic upload interface with drag & drop
2. **File Browser**: Display uploaded files with status
3. **URL Input**: Web URL addition and processing
4. **Integration Cards**: Connect external services
5. **Search & Filter**: Find and organize content

## **Key Features**

### **File Upload**
- **Drag & Drop**: Direct file dropping into upload area
- **Multiple Selection**: Batch upload capability
- **Progress Tracking**: Real-time upload progress
- **File Validation**: Size and type restrictions
- **Error Handling**: Upload failure recovery

### **Content Management**
- **File Organization**: Hierarchical folder structure
- **Search & Discovery**: Find content across all sources
- **Status Tracking**: Processing and completion status
- **Bulk Operations**: Multi-file management actions

This specification provides a **focused implementation roadmap** for building a modern file management interface with shadcn/ui components, prioritizing core upload functionality and content organization.