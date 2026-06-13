#!/usr/bin/env python3
"""
Browser Control REST API Server
Low-level browser automation endpoints
"""

import os
import asyncio
import base64
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from ml.agents import BrowserAgent

app = FastAPI(
    title="DevForge Browser Control API",
    description="Low-level browser automation API",
    version="2.0.0"
)

# Global browser instance
browser_instance: Optional[BrowserAgent] = None


class NavigateRequest(BaseModel):
    """Request to navigate to a URL"""
    url: str
    timeout: int = 30000


class ClickRequest(BaseModel):
    """Request to click an element"""
    selector: str
    timeout: int = 5000


class FillRequest(BaseModel):
    """Request to fill a form field"""
    selector: str
    text: str
    timeout: int = 5000


class ExtractRequest(BaseModel):
    """Request to extract page content"""
    selector: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize browser on startup"""
    global browser_instance
    try:
        browser_instance = BrowserAgent()
        await browser_instance.start()
        print("✓ Browser initialized on startup")
    except Exception as e:
        print(f"✗ Failed to initialize browser: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close browser on shutdown"""
    global browser_instance
    if browser_instance:
        try:
            await browser_instance.stop()
            print("✓ Browser closed")
        except Exception as e:
            print(f"✗ Failed to close browser: {e}")


def get_browser() -> BrowserAgent:
    """Get the global browser instance"""
    global browser_instance
    if not browser_instance:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    return browser_instance


# Health check

@app.get("/health")
async def health_check():
    """Check browser API health"""
    return {
        "status": "healthy",
        "service": "Browser Control API",
        "browser_ready": browser_instance is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Navigation

@app.post("/api/browser/navigate")
async def navigate(request: NavigateRequest):
    """Navigate to a URL"""
    browser = get_browser()

    try:
        success = await browser.navigate(request.url)

        if success:
            return {
                "status": "success",
                "url": request.url,
                "message": f"Navigated to {request.url}"
            }
        else:
            raise HTTPException(status_code=400, detail="Navigation failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Screenshots

@app.get("/api/browser/screenshot")
async def take_screenshot():
    """Take a screenshot of the current page"""
    browser = get_browser()

    try:
        screenshot_b64 = await browser.screenshot()

        if not screenshot_b64:
            raise HTTPException(status_code=500, detail="Failed to capture screenshot")

        return {
            "status": "success",
            "screenshot": screenshot_b64,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Page content

@app.get("/api/browser/content")
async def get_page_content():
    """Get current page content and structure"""
    browser = get_browser()

    try:
        content = await browser.get_page_content()

        if not content:
            raise HTTPException(status_code=500, detail="Failed to get page content")

        return {
            "status": "success",
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Clicking

@app.post("/api/browser/click")
async def click_element(request: ClickRequest):
    """Click an element on the page"""
    browser = get_browser()

    try:
        success = await browser.click(request.selector)

        if success:
            return {
                "status": "success",
                "selector": request.selector,
                "message": f"Clicked {request.selector}"
            }
        else:
            raise HTTPException(status_code=400, detail="Click failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Form filling

@app.post("/api/browser/fill")
async def fill_field(request: FillRequest):
    """Fill a form field"""
    browser = get_browser()

    try:
        success = await browser.fill(request.selector, request.text)

        if success:
            return {
                "status": "success",
                "selector": request.selector,
                "message": f"Filled {request.selector}"
            }
        else:
            raise HTTPException(status_code=400, detail="Fill failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/browser/fill-form")
async def fill_form(request: Dict[str, str]):
    """Fill multiple form fields"""
    browser = get_browser()

    results = []

    try:
        for selector, text in request.items():
            success = await browser.fill(selector, text)
            results.append({
                "selector": selector,
                "success": success
            })

        return {
            "status": "success",
            "results": results,
            "message": f"Filled {len(results)} fields"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Content extraction

@app.post("/api/browser/extract")
async def extract_content(request: ExtractRequest):
    """Extract content from the page"""
    browser = get_browser()

    try:
        content = await browser.get_page_content()

        if request.selector:
            # Filter to specific element
            elements = [e for e in content.get("elements", [])
                       if request.selector in str(e.get("className", ""))]
        else:
            elements = content.get("elements", [])

        return {
            "status": "success",
            "elements": elements,
            "count": len(elements)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Evaluate JavaScript

@app.post("/api/browser/evaluate")
async def evaluate_javascript(request: Dict[str, str]):
    """Evaluate JavaScript code on the page"""
    browser = get_browser()

    try:
        code = request.get("code", "")

        if not code:
            raise HTTPException(status_code=400, detail="Code is required")

        # Use the page's evaluate method directly
        result = await browser.page.evaluate(code)

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Status endpoints

@app.get("/api/browser/url")
async def get_current_url():
    """Get the current page URL"""
    browser = get_browser()

    try:
        content = await browser.get_page_content()
        url = content.get("url", "")

        return {
            "status": "success",
            "url": url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/browser/title")
async def get_page_title():
    """Get the current page title"""
    browser = get_browser()

    try:
        content = await browser.get_page_content()
        title = content.get("title", "")

        return {
            "status": "success",
            "title": title
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Session management

@app.post("/api/browser/session/start")
async def start_session():
    """Start a new browser session"""
    global browser_instance

    try:
        if browser_instance and browser_instance.page:
            return {
                "status": "already_running",
                "message": "Browser session already active"
            }

        browser_instance = BrowserAgent()
        await browser_instance.start()

        return {
            "status": "success",
            "message": "Browser session started"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/browser/session/end")
async def end_session():
    """End the current browser session"""
    global browser_instance

    try:
        if browser_instance:
            await browser_instance.stop()
            browser_instance = None

        return {
            "status": "success",
            "message": "Browser session ended"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/browser/session")
async def get_session_status():
    """Get browser session status"""
    return {
        "status": "active" if browser_instance and browser_instance.page else "inactive",
        "browser_ready": browser_instance is not None,
        "timestamp": datetime.utcnow().isoformat()
    }


# Root endpoint

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "DevForge Browser Control API",
        "version": "2.0.0",
        "documentation": "/docs",
        "health": "/health",
        "session": "/api/browser/session",
        "actions": [
            "POST /api/browser/navigate",
            "GET /api/browser/screenshot",
            "GET /api/browser/content",
            "POST /api/browser/click",
            "POST /api/browser/fill",
            "POST /api/browser/extract"
        ]
    }


if __name__ == "__main__":
    port = int(os.getenv("BROWSER_API_PORT", 8002))
    print(f"Starting Browser Control API on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
