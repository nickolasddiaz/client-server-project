# CNT3004 – Socket-Based Networked File Sharing Cloud Server

## 📋 Table of Contents
- [Project Overview](#project-overview)
- [System Requirements](#system-requirements)
- [Architecture & Design](#architecture--design)
- [Supported Operations](#supported-operations)
- [Performance Metrics](#performance-metrics)
- [Submission Requirements](#submission-requirements)

---

## Project Overview

### Objective
Design, implement, and evaluate a distributed file sharing system using a server-client architecture. The system facilitates efficient and secure file transfer between multiple clients connected to a central server.

### Key Features
- ✅ Multithreaded server supporting concurrent client connections
- ✅ Secure authentication with encrypted credentials
- ✅ Support for large files (text: 25MB+, audio: 1GB+, video: 2GB+)
- ✅ Comprehensive file operations (upload, download, delete, directory management)
- ✅ Real-time performance monitoring and analytics

---

## System Requirements

### Architecture Constraints
- **Distributed Deployment**: Server and clients **must run on separate computers**
- **Protocol**: TCP or UDP for reliable file transmission (FTP is **not permitted**)
- **Threading**: Server must handle multiple concurrent client connections
- **Authentication**: Secure mechanism with encrypted password transmission

### Supported File Types & Minimum Sizes
| File Type | Minimum Size |
|-----------|--------------|
| Text      | 25 MB        |
| Audio     | 1 GB         |
| Video     | 2 GB         |

---

## Architecture & Design

### Server-Side Components
```
📦 Server Application
 ├─ Multithreaded connection handler
 ├─ File system manager with naming conventions (e.g., TS001 for Text-Server)
 ├─ Authentication & authorization module
 ├─ Network protocol implementation (TCP/UDP)
 └─ Performance statistics collector
```

**Key Responsibilities:**
- Accept and manage multiple client connections simultaneously
- Authenticate users with encrypted credentials
- Handle file storage with logical naming conventions
- Prevent duplicate file conflicts (prompt for overwrite)
- Track and log performance metrics

### Client-Side Components
```
📱 Client Application
 ├─ User interface for file operations
 ├─ Network communication module
 ├─ File transfer handler (upload/download)
 └─ Status feedback system
```

**Key Responsibilities:**
- Provide intuitive command-line interface
- Establish secure connection to server
- Execute file operations with real-time feedback
- Display transfer progress and error messages

### Network Analysis Module
```
📊 Analytics Component
 ├─ Statistics collector (server & client)
 ├─ Data storage (dictionary/dataframe)
 └─ Offline analysis export
```

**Tracked Metrics:**
- Upload/download data rates (MB/s)
- File transfer completion times
- System response times
- Connection statistics

---

## Supported Operations

### Connection & Authentication
```bash
Connect [server_IP] [Port]
```
Initiates secure connection with username/password authentication (encrypted transmission).

### File Management Commands

| Command | Syntax | Description |
|---------|--------|-------------|
| **Upload** | `Upload [server_IP]` | Upload files to server (prompts if file exists) |
| **Download** | `Download [filename]` | Download files from server (error if not found) |
| **Delete** | `Delete [filename]` | Remove files from server (error if in use/not found) |
| **Dir** | `Dir` | List all files and subdirectories in server storage |
| **Subfolder** | `Subfolder {create\|delete} [path/directory]` | Create or delete subdirectories |

---

## Performance Metrics

The system collects and analyzes:
- **Data Transfer Rates**: Upload and download speeds in MB/s
- **Transfer Times**: Total time for file operations
- **Response Times**: System latency and responsiveness
- **Load Testing**: Performance under various concurrent connection scenarios

### Error Handling
- Graceful exception management
- Informative client-side error messages
- Server-side logging of errors and warnings

---

## Submission Requirements

### 📄 1. Project Report (DOC/PDF)
**Required Sections:**
- **Cover Page**: Project name, date, course section, team member names
- **Introduction & Objectives** (1 page)
- **System Architecture & Design** (1-2 pages)
- **Implementation Details** (3 pages)
- **Experimental Results & Analysis** (3+ pages)
  - Captioned diagrams, graphs, and screenshots
  - 1-2 paragraph analysis for each visual
- **Challenges Faced** (1-2 paragraphs)
- **Individual Learnings** (1-2 paragraphs per team member)
- **Contribution Table** (activity type & effort percentage per member)
- **Conclusions & Future Work** (3 paragraphs)

### 💻 2. Source Code
Submit **3 Python modules minimum**:
- `server.py` – Server application with multithreading
- `client.py` – Client application with UI
- `analytics.py` – Performance monitoring module

**Code Requirements:**
- Well-commented and organized
- Clear variable naming
- Modular design with reusable functions

### 🎥 3. Video Presentation (8-12 minutes, MP4 format)
**Content Requirements:**
- Discussion of all components (server, analytics, client) with equal narration distribution
- **Code Snippets** demonstrating:
  - Authorization method (encryption/obfuscation)
  - Analytics data storage implementation
  - Server-side logic
  - Client command input processing
  - Socket setup
- **Live Demonstration** showing:
  - Connect operation
  - Upload operation
  - Download operation
  - Dir operation
  - Subfolder create/delete operations

**Technical Requirements:**
- Screen recording with audible narration (faces not required)
- MP4 container format
- Use Sim Lab for video production assistance

### 🎯 4. In-Class Demonstration
**Week 14** (November 17-23): Live demonstration to TA during class hours
- Demonstrations follow sequential group order
- No slides required
- Be prepared to run code and answer questions

---

## Security Considerations

- **Password Encryption**: No clear-text password transmission
- **Authentication**: Secure user verification before file access
- **Access Control**: Restrict unauthorized system access
- **Data Integrity**: Ensure files are not corrupted during transfer

---

## Getting Started

### Prerequisites
- Python 3.x
- Network connectivity between server and client machines
- Sufficient storage for test files (2GB+ recommended)

### Quick Start
```bash
# Start server
python server.py

# Connect client
python client.py
```