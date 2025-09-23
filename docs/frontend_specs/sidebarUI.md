# **Sidebar Navigation - Implementation Specification**

This specification outlines a **modern sidebar navigation interface** built with shadcn/ui components, featuring organization selector, navigation menu, and user profile management.

## **Core Sidebar Architecture**

### **Main Layout Structure**

**Primary Components:**
- **SidebarProvider**: Context provider for sidebar state management
- **Sidebar**: Main sidebar container with collapsible functionality
- **SidebarHeader**: Organization selector and workspace management
- **SidebarContent**: Scrollable navigation menu
- **SidebarFooter**: User profile and account management

**Layout Structure:**
```
Sidebar Navigation
├── SidebarProvider (Context)
├── Sidebar
│   ├── SidebarHeader
│   │   └── Organization Selector
│   ├── SidebarContent
│   │   ├── Navigation Menu
│   │   └── Quick Actions
│   └── SidebarFooter
│       └── User Profile
└── SidebarTrigger (Toggle Button)
```

### **Key Interface Elements**

**Organization Selector (Header):**
- **Workspace Dropdown**: Select between different organizations/workspaces
- **Organization Name**: Current workspace display
- **Switch Organization**: Quick access to organization management

**Navigation Menu (Content):**
- **Dashboard**: Overview and analytics
- **AI Chat**: Primary chat interface
- **Knowledge Sources**: File and content management
- **Settings**: Application configuration
- **Analytics**: Usage and performance metrics

**User Profile (Footer):**
- **User Avatar**: Profile picture with fallback
- **User Name**: Display name (editable)
- **User Description**: Role/title (editable)
- **Account Actions**: Profile settings, billing, sign out

## **Component Implementation**

### **Main Sidebar Component**
```tsx
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"

export function SidebarLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1">
        <SidebarTrigger />
        {children}
      </main>
    </SidebarProvider>
  )
}
```

### **App Sidebar Component**
```tsx
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
} from "@/components/ui/sidebar"
import { OrganizationSelector } from "@/components/sidebar/organization-selector"
import { NavigationMenu } from "@/components/sidebar/navigation-menu"
import { UserProfile } from "@/components/sidebar/user-profile"

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon" className="border-r">
      <SidebarHeader>
        <OrganizationSelector />
      </SidebarHeader>
      <SidebarContent>
        <NavigationMenu />
      </SidebarContent>
      <SidebarFooter>
        <UserProfile />
      </SidebarFooter>
    </Sidebar>
  )
}
```

### **Organization Selector Component**
```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { ChevronDown, Building2 } from "lucide-react"

export function OrganizationSelector() {
  const organizations = [
    { id: "1", name: "Acme Inc", role: "Owner" },
    { id: "2", name: "Acme Corp", role: "Admin" },
    { id: "3", name: "Startup Co", role: "Member" },
  ]

  const currentOrg = organizations[0]

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton size="lg" className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
              <Building2 className="h-4 w-4" />
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{currentOrg.name}</span>
                <span className="truncate text-xs">{currentOrg.role}</span>
              </div>
              <ChevronDown className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            side="bottom"
            align="start"
            sideOffset={4}
          >
            {organizations.map((org) => (
              <DropdownMenuItem key={org.id} className="gap-2 p-2">
                <Building2 className="h-4 w-4" />
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">{org.name}</span>
                  <span className="truncate text-xs">{org.role}</span>
                </div>
              </DropdownMenuItem>
            ))}
            <DropdownMenuItem className="gap-2 p-2">
              <Building2 className="h-4 w-4" />
              <span>Create organization</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
```

### **Navigation Menu Component**
```tsx
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import {
  Home,
  MessageSquare,
  FolderOpen,
  Settings,
  BarChart3,
} from "lucide-react"
import Link from "next/link"

export function NavigationMenu() {
  const navigationItems = [
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: Home,
    },
    {
      title: "AI Chat",
      url: "/chat",
      icon: MessageSquare,
    },
    {
      title: "Knowledge Sources",
      url: "/knowledge",
      icon: FolderOpen,
    },
    {
      title: "Analytics",
      url: "/analytics",
      icon: BarChart3,
    },
    {
      title: "Settings",
      url: "/settings",
      icon: Settings,
    },
  ]

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Platform</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          {navigationItems.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild>
                <Link href={item.url}>
                  <item.icon />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}
```

### **User Profile Component**
```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { ChevronUp, User, Settings, LogOut } from "lucide-react"

export function UserProfile() {
  const user = {
    name: "John Doe",
    email: "john@example.com",
    role: "Product Manager",
    avatar: "/user-avatar.jpg"
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <Avatar className="h-8 w-8 rounded-lg">
                <AvatarImage src={user.avatar} alt={user.name} />
                <AvatarFallback className="rounded-lg">
                  {user.name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{user.name}</span>
                <span className="truncate text-xs">{user.role}</span>
              </div>
              <ChevronUp className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
            side="top"
            align="end"
            sideOffset={4}
          >
            <DropdownMenuItem className="gap-2 p-2">
              <User className="h-4 w-4" />
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-semibold">{user.name}</span>
                <span className="truncate text-xs">{user.email}</span>
              </div>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 p-2">
              <User className="h-4 w-4" />
              <span>Edit Profile</span>
            </DropdownMenuItem>
            <DropdownMenuItem className="gap-2 p-2">
              <Settings className="h-4 w-4" />
              <span>Account Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 p-2 text-red-600">
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
```

## **User Profile Editing**

### **Profile Edit Modal**
```tsx
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Camera } from "lucide-react"

export function ProfileEditModal({ open, onOpenChange }: ProfileEditModalProps) {
  const [name, setName] = useState("John Doe")
  const [role, setRole] = useState("Product Manager")
  const [description, setDescription] = useState("Leading product development and strategy")

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>
        <div className="space-y-6">
          <div className="flex flex-col items-center space-y-4">
            <div className="relative">
              <Avatar className="h-20 w-20">
                <AvatarImage src="/user-avatar.jpg" />
                <AvatarFallback className="text-lg">
                  {name.split(' ').map(n => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <Button
                size="icon"
                className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full"
              >
                <Camera className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Input
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Enter your role"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Tell us about yourself"
                rows={3}
              />
            </div>
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={() => onOpenChange(false)}>
              Save Changes
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

## **State Management**

### **Sidebar State**
```tsx
interface SidebarState {
  isOpen: boolean
  isMobile: boolean
  currentOrganization: Organization
  user: User
}

interface Organization {
  id: string
  name: string
  role: string
  avatar?: string
}

interface User {
  id: string
  name: string
  email: string
  role: string
  description?: string
  avatar?: string
}
```

## **Responsive Behavior**

### **Collapsible States**
- **Desktop**: Collapses to icons when closed
- **Mobile**: Slides in as overlay when opened
- **Tablet**: Adapts based on screen size

### **Breakpoint Behavior**
- **Mobile (< 768px)**: Overlay sidebar with backdrop
- **Tablet (768px - 1024px)**: Collapsible sidebar
- **Desktop (> 1024px)**: Full sidebar with icon collapse

## **Implementation Priority**

1. **Core Sidebar**: Basic sidebar with provider and trigger
2. **Navigation Menu**: Main navigation items with routing
3. **Organization Selector**: Workspace switching functionality
4. **User Profile**: Profile display and basic actions
5. **Profile Editing**: Modal for editing user information
6. **Responsive Design**: Mobile and tablet adaptations

## **Key Features**

### **Navigation**
- **Collapsible Sidebar**: Icon-only mode for space efficiency
- **Active State**: Current page highlighting
- **Keyboard Shortcuts**: Cmd/Ctrl + B to toggle
- **Persistent State**: Remembers open/closed state

### **Organization Management**
- **Multi-tenant Support**: Switch between organizations
- **Role Display**: Show user role in current organization
- **Quick Switch**: Dropdown for organization selection

### **User Profile**
- **Editable Information**: Name, role, and description
- **Avatar Management**: Profile picture upload
- **Account Actions**: Settings, billing, sign out
- **Real-time Updates**: Immediate UI updates on changes

This specification provides a **comprehensive implementation roadmap** for building a modern sidebar navigation with shadcn/ui components, featuring organization management and user profile editing capabilities.
