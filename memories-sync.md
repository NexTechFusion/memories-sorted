# Ingestion Strategy: The "Zero-Effort" Photo Hub

This document outlines the strategic pivot for Phase 3: transitioning from a manual photo viewer to a high-volume, automated aggregation hub for 10K+ photos across multiple providers.

## 核心理念 (Core Philosophy)
**"Laziness as a Feature"**: Users should not "upload" photos; the hub should "harvest" them from where life already happens.

---

## 1. The Ingest "Pipes" (Connectors)

### 🛋️ GDrive "Mirror" (The Moat)
*   **Workflow**: Headless OAuth sync. The hub "watches" a specific GDrive folder.
*   **Lazy Factor**: You already use GDrive on your phone. Moving a photo to the "Family" folder in the native GDrive app makes it appear in the AI Hub automatically.
*   **Scale**: Handles the 10K+ legacy backlog via background harvester.

### 💨 Telegram/WhatsApp "Snapshot" (Hot Sync)
*   **Workflow**: Dedicated private bot.
*   **Lazy Factor**: Forward any photo/gallery from a family chat to the bot.
*   **Intelligence**: The bot replies with recognized people and a generated caption based on the chat context.

### 🏠 Local Archivist (SMB/NAS Scanner)
*   **Workflow**: Network-attached storage (Synology/QNAP) scanning.
*   **Lazy Factor**: Dump photos from a camera SD card to your NAS; the hub "shadow-follows" the directory and indexes them in the background.

### 📱 "One-Tap" Mobile Intent
*   **Workflow**: iOS Shortcut or Android Share Intent.
*   **Lazy Factor**: Long-press a photo in your native gallery → "Send to Memories". Bypasses cloud walled gardens.

---

## 2. The "Brain" (Deduplication & Enrichment)

To act as a hub, the system must handle the same photo arriving from multiple sources (e.g., Phone + GDrive + Telegram).

*   **Level 1 (Hash)**: Exact SHA-256 check for binary identity.
*   **Level 2 (Perceptual)**: **pHash (Perceptual Hashing)** checks for visual similarity. If a high-res GDrive version and a compressed Telegram version match (>95%), the hub merges them, keeping the highest resolution original.
*   **Level 3 (Context)**: Merges metadata (EXIF from GDrive + Chat captions from Telegram) into a single "Master Record".

---

## 3. Architecture & Ecosystem (MCP Sidecar)

The Hub should be decoupled through the **Model Context Protocol (MCP)**.

*   **Ingestion is Lazy**: Bots and scanners fill the pool.
*   **Consumption is Invisible**: You don't open the "Memories" app to find a photo. You ask your AI (Claude/OpenClaw): *"Find that trip to Turkey last year."*
*   **Hub as Provider**: As an MCP server, it "serves" photos and metadata to any authorized agent, eliminating the need for manual organization.

---

## 4. Storage vs. Search Strategy

*   **Hybrid Storage**: The VPS stores **Thumbnails + CLIP/Face Vectors** (Low storage cost). 
*   **Remote Linking**: The "Master Record" links back to the original source (GDrive URL, NAS path, or cold storage) to avoid filling VPS disk space with 100GB of raw binaries.

---

## Phase 3 Roadmap (The "Lazy" Build)

| Task | Priority | Focus |
| --- | --- | --- |
| **3.1** Telegram Bot Ingest | 🔥 High | Instant dopamine / daily use. |
| **3.2** Headless GDrive Sync | 🔥 High | Bulk processing of 10K legacy photos. |
| **3.3** pHash Deduplication | 🟡 Med | Cleanliness across providers. |
| **3.4** MCP Server Wrapper | 🟡 Med | AI-native cross-app utility. |
| **3.5** Background Worker UI | 🔵 Low | Visibility into sync progress. |
