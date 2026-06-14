# MindStudio Agent Skills Plugin — Installation & Discovery Report

## Installation Status
✅ **Installed**: `@mindstudio-ai/agent@0.1.66` via npm  
Available as CLI tool: `mindstudio` command  
Type: ESM module with full TypeScript definitions

## What Just Became Possible

### 1. **178 Pre-Built AI & Integration Actions**
- More than just models — entire ecosystems of capabilities
- Single API key unlocks all integrations (no scattered credentials)
- Real-time streaming for long-running operations (video generation, scraping, etc.)

### 2. **Most Surprising Capabilities** 🤯

#### Social Media Intelligence (not common in other SDKs)
```
ScrapeInstagram → Comments, Mentions, Posts, Profiles, Reels
ScrapeFacebook → Pages, Individual Posts  
ScrapeLinkedIn → Company Profiles, Individual Profiles
ScrapeX (Twitter) → Posts, Profiles
SearchYoutube → Videos + Trending Searches
FetchYoutube → Captions, Comments, Channel Data
```
**Use Case for DevForge**: Auto-find code examples/tutorials on social platforms for training context

#### Podcast Content Extraction (unique in AI SDKs)
```
ParticlePodcasts:
  - FindMentions (search for company/person mentions in episodes)
  - GetEpisodeTranscript (full episode text)
  - SearchDialogue (search within episode transcripts)
  - SearchPodcasts (find relevant shows)
```
**Use Case for DevForge**: Index coding podcasts, extract best practices, find expert discussions

#### Advanced Video Manipulation (beyond text/code generation)
```
GenerateVideo, GenerateLipsync, Generate3dModel
VideoFaceSwap, VideoRemoveBackground, VideoRemoveWatermark
AddSubtitlesToVideo, MergeVideos, ResizeVideo, TrimMedia, DownloadVideo
```
**Use Case for DevForge**: Auto-generate tutorial videos of code changes

#### Real-Time Web Research (beyond simple search)
```
SearchGoogle, SearchGoogleNews, SearchGoogleTrends
SearchPerplexity, SearchYoutubeTrends
YouDotCom (4 actions) → Finance research, live news, web search, page content
```
**Use Case for DevForge**: Real-time trend analysis before suggesting code changes

#### No-Code Automation Bridging (meta-powerful)
```
N8nRunNode (execute n8n.io workflows)
MakeDotComRunScenario (execute Make.com scenarios)
PostToZapier (trigger Zapier automations)
```
**Use Case for DevForge**: Trigger external workflows when code generation completes

---

## What This Means for DevForge

### Current DevForge Architecture
- Hugging Face model discovery ✅
- Multi-model code generation ✅
- GitHub PR creation ✅

### What MindStudio Unlocks (Next Level)
1. **Expanded Model Access** → 200+ models vs Hugging Face alone
2. **Notification Ecosystem** → Slack, Email, Discord, Telegram, Teams
3. **Data Enrichment** → Scrape docs, Stack Overflow, GitHub trending for context
4. **Workflow Automation** → Trigger CI/CD, testing, deployment pipelines
5. **Content Generation** → Generate tutorial videos of the changes
6. **Analytics** → Search what's trending in code/tech to suggest timely changes

### Immediate Integration Ideas
1. **Slack Notifications** → "CodeGen completed, PR ready for review"
2. **Gmail Integration** → Send PR links to stakeholders
3. **Real-Time Search** → Find latest coding trends before suggesting changes
4. **LinkedIn Posting** → Auto-announce major code improvements

---

## Technical Setup Barrier

⚠️ **Requires**: MindStudio account + API key  
Without API key, the SDK is installed but non-functional.

```typescript
// Would need this to activate:
const agent = new MindStudioAgent({
  apiKey: process.env.MINDSTUDIO_API_KEY
});

// Then unlimited access to:
await agent.executeStep('GenerateImage', { prompt: '...' });
await agent.executeStep('ScrapeUrl', { url: '...' });
await agent.executeStep('PostToSlackChannel', { ... });
// ... 175 more actions
```

---

## Top 5 Surprises

1. **Instagram/Facebook/LinkedIn Scraping** — Can extract posts, comments, entire profiles (compliance permitting)
2. **Podcast Transcript Search** — Find expert discussions about any topic across 100k+ episodes
3. **Video Face-Swap & Deepfake Tools** — Professional video manipulation in one step
4. **Real-Time Trend Analysis** — Know what's trending on Google/YouTube before making suggestions
5. **No-Code Platform Bridges** — Execute n8n & Make.com workflows as simple function calls

These go beyond "wrapper SDKs" — this is infrastructure for building unified automation agents.

---

## Complete List of 178 Available Step Types

### Categories Breakdown

**Email & Messaging (20)**
CreateGmailDraft, DeleteGmailEmail, DiscordEditMessage, DiscordSendFollowUp, DiscordSendMessage, FetchSlackChannelHistory, GetGmailAttachments, GetGmailDraft, GetGmailEmail, GetGmailUnreadCount, ListGmailDrafts, ListGmailLabels, ListRecentGmailEmails, PostToLinkedIn, PostToSlackChannel, PostToX, ReplyToGmailEmail, SearchGmailEmails, SendEmail, SendGmailDraft, SendGmailMessage, SendSMS, TelegramEditMessage, TelegramReplyToMessage, TelegramSendAudio, TelegramSendFile, TelegramSendImage, TelegramSendMessage, TelegramSendVideo, UpdateGmailLabels

**Data & Databases (15)**
AirtableCreateUpdateRecord, AirtableDeleteRecord, AirtableGetRecord, AirtableGetTableRecords, CodaCreateUpdatePage, CodaCreateUpdateRow, CodaFindRow, CodaGetPage, CodaGetTableRows, CreateDataSource, CreateGoogleSheet, DeleteDataSource, DeleteDataSourceDocument, DeleteGoogleSheetRows, FetchDataSourceDocument, FetchGoogleSheet, GetGoogleSheetInfo, NotionCreatePage, NotionUpdatePage, QueryAppDatabase, QueryDataSource, QueryExternalDatabase, UpdateGoogleSheet, UploadDataSourceDocument

**Media Generation & Manipulation (25)**
AddSubtitlesToVideo, AnalyzeImage, AnalyzeVideo, CaptureThumbnail, ConvertPdfToImages, DownloadVideo, EnhanceImageGenerationPrompt, EnhanceVideoGenerationPrompt, ExtractAudioFromVideo, Generate3dModel, GenerateChart, GenerateImage, GenerateLipsync, GenerateMusic, GeneratePdf, GenerateStaticVideoFromImage, GenerateVideo, ImageFaceSwap, ImageRemoveWatermark, InsertVideoClips, MergeAudio, MergeVideos, MixAudioIntoVideo, MuteVideo, RemoveBackgroundFromImage, ResizeVideo, TextToSpeech, TrimMedia, UpscaleImage, UpscaleVideo, VideoFaceSwap, VideoRemoveBackground, VideoRemoveWatermark, WatermarkImage, WatermarkVideo

**Web Scraping & Search (50+)**
FetchYoutubeCaptions, FetchYoutubeChannel, FetchYoutubeComments, FetchYoutubeVideo, ParticlePodcastsFindMentions, ParticlePodcastsGetEpisode, ParticlePodcastsGetEpisodeTranscript, ParticlePodcastsSearchCompanies, ParticlePodcastsSearchDialogue, ParticlePodcastsSearchPodcasts, ScrapeFacebookPage, ScrapeFacebookPosts, ScrapeInstagramComments, ScrapeInstagramMentions, ScrapeInstagramPosts, ScrapeInstagramProfile, ScrapeInstagramReels, ScrapeLinkedInCompany, ScrapeLinkedInProfile, ScrapeMetaThreadsProfile, ScrapeUrl, ScrapeXPost, ScrapeXProfile, ScreenshotUrl, SearchGoogle, SearchGoogleCalendarEvents, SearchGoogleDrive, SearchGoogleImages, SearchGoogleNews, SearchGoogleTrends, SearchPerplexity, SearchXPosts, SearchYoutube, SearchYoutubeTrends, YouDotComFinanceResearch, YouDotComGetPageContent, YouDotComLiveNews, YouDotComWebResearch, YouDotComWebSearch

**CRM & Business (12)**
ActiveCampaignAddNote, ActiveCampaignCreateContact, HubspotCreateCompany, HubspotCreateContact, HubspotGetCompany, HubspotGetContact, HunterApiCompanyEnrichment, HunterApiDomainSearch, HunterApiEmailFinder, HunterApiEmailVerification, HunterApiPersonEnrichment

**Automation & Workflow Bridging (5)**
Logic, MakeDotComRunScenario, N8nRunNode, PostToZapier, RunFromConnectorRegistry, RunPackagedWorkflow, SetRunTitle, SetVariable, UserMessage

**AI & Content Intelligence (8)**
DetectChanges, DetectPII, ExtractText, PeopleSearch, RedactPII, TranscribeAudio, EnrichPerson, CheckAppRole

**Calendar & Files (8)**
CreateGoogleCalendarEvent, CreateGoogleDoc, DeleteGoogleCalendarEvent, GetGoogleCalendarEvent, GetGoogleDriveFile, ListGoogleCalendarEvents, ListGoogleDriveFiles, SearchGoogleCalendarEvents, SearchGoogleDrive, UpdateGoogleCalendarEvent, UpdateGoogleDoc

**3D & Specialized AI (8)**
Generate3dModel, MeshyAnimate, MeshyImageTo3d, MeshyRemesh, MeshyRig, MeshyTexture, MeshyTextTo3d
