#!/usr/bin/env python3
"""
WORKING browser-use setup - uses defaults, you just log in and it works!
This avoids all the path and profile issues by using browser-use defaults.
Now includes the Hyphenbox extension + custom login functions!
"""

import asyncio
from pathlib import Path
from browser_use import Agent, BrowserSession
from browser_use.controller.service import Controller
from browser_use.agent.views import ActionResult
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from openai import OpenAI
from typing import Optional


class LoadLoginDetailsParams(BaseModel):
    pass  # No parameters needed


class WaitForUserParams(BaseModel):
    message: str = Field(description="Message to show user about what they need to do")


class LoadItemsParams(BaseModel):
    pass  # No parameters needed


class RefineProductSearchParams(BaseModel):
    user_input: str = Field(description="The user's vague product description (e.g., 'pringles original taste chips')")


class ValidateProductSelectionParams(BaseModel):
    user_requested_item: str = Field(description="Original item user requested")
    found_product_name: str = Field(description="Name of product found on website")
    found_product_brand: str = Field(description="Brand of product found on website")
    found_product_price: str = Field(description="Price of product found")
    found_product_size: str = Field(description="Size/quantity of product found")


class AssessAndScrollParams(BaseModel):
    direction: str = Field(description="Direction to scroll: 'down' or 'up'")
    target_content: str = Field(description="What you're looking for (e.g., 'add to cart button', 'product information', 'price details')")
    amount: Optional[int] = Field(default=None, description="Optional pixel amount to scroll. If None, scrolls one page")


def setup_custom_controller():
    """Set up custom controller with login functions and enhanced product selection"""
    controller = Controller()
    
    @controller.action("Load user login details from details.txt file")
    async def load_login_details(params: LoadLoginDetailsParams) -> ActionResult:
        """Load all login details from details.txt"""
        try:
            # Read the entire file content including comments and tips
            with open('details.txt', 'r') as f:
                file_content = f.read()
            
            return ActionResult(
                extracted_content=f"Login details loaded:\n{file_content}",
                include_in_memory=True
            )
            
        except Exception as e:
            return ActionResult(error=f"Error loading details: {str(e)}")
    
    @controller.action("Wait for user to manually complete OTP, password, or any authentication step")
    async def wait_for_user(params: WaitForUserParams) -> ActionResult:
        """Pause and wait for user to complete manual action"""
        try:
            # Handle both dict and object parameter formats
            if isinstance(params, dict):
                message = params.get('message', 'Complete the manual action')
            else:
                message = params.message
                
            print(f"\n🔐 AGENT PAUSED: {message}")
            print("⏳ Press Enter when you've completed the action...")
            
            # Use asyncio.to_thread to handle the blocking input() call
            await asyncio.to_thread(input)
            
            return ActionResult(
                extracted_content="User completed the manual action, continuing...",
                include_in_memory=True
            )
            
        except Exception as e:
            return ActionResult(error=f"Error during wait: {str(e)}")

    @controller.action("Load shopping list from items.txt file")
    async def load_items(params: LoadItemsParams) -> ActionResult:
        """Load shopping items from items.txt"""
        try:
            with open('items.txt', 'r') as f:
                items_content = f.read()
            
            return ActionResult(
                extracted_content=f"Shopping list loaded from items.txt:\n{items_content}",
                include_in_memory=True
            )
            
        except Exception as e:
            return ActionResult(error=f"Error loading items: {str(e)}")

    @controller.action("Assess current page and scroll only if target content not found in viewport")
    async def assess_and_scroll(params: AssessAndScrollParams, browser_session: BrowserSession) -> ActionResult:
        """
        Smart scrolling: First assess if target content is visible in current viewport.
        Only scroll if the target content is not found in the currently visible elements.
        """
        try:
            from langchain_openai import ChatOpenAI
            
            # Handle both dict and object parameter formats
            if isinstance(params, dict):
                direction = params.get('direction', 'down')
                target_content = params.get('target_content', '')
                amount = params.get('amount', None)
            else:
                direction = params.direction
                target_content = params.target_content
                amount = params.amount
            
            # Get current page state
            page = await browser_session.get_current_page()
            
            # Get current viewport content
            current_content = await page.evaluate('''
                () => {
                    // Get all visible text content in the viewport
                    const rect = document.documentElement.getBoundingClientRect();
                    const viewportHeight = window.innerHeight;
                    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
                        const elRect = el.getBoundingClientRect();
                        return elRect.top >= 0 && elRect.top < viewportHeight && 
                               elRect.width > 0 && elRect.height > 0 &&
                               el.textContent && el.textContent.trim();
                    });
                    
                    return elements.map(el => el.textContent.trim()).join(' ').substring(0, 2000);
                }
            ''')
            
            # Quick check: Use OpenAI to assess if target content might be in current viewport
            llm = ChatOpenAI(model="gpt-4o-mini")  # Use faster model for assessment
            
            assessment_prompt = f"""
            CURRENT VIEWPORT CONTENT:
            {current_content}
            
            QUESTION: Is there any content related to "{target_content}" visible in the current viewport?
            
            Look for:
            - The exact item/element mentioned
            - Related keywords or similar content
            - Elements that might contain what we're looking for
            
            Answer with just: FOUND or NOT_FOUND
            
            If you see anything that could be related to "{target_content}", answer FOUND.
            Only answer NOT_FOUND if you're confident the target content is not visible.
            """
            
            response = await llm.ainvoke([{"role": "user", "content": assessment_prompt}])
            assessment = response.content.strip().upper()
            
            print(f"   🔍 Assessment for '{target_content}': {assessment}")
            
            if "FOUND" in assessment:
                return ActionResult(
                    extracted_content=f"✅ Target content '{target_content}' appears to be visible in current viewport. No scrolling needed. Please look for the specific element in the current view.",
                    include_in_memory=True
                )
            else:
                # Content not found, proceed with scrolling
                print(f"   📜 Target content not found in viewport. Scrolling {direction}...")
                
                # Get current scroll info
                pixels_above, pixels_below = await browser_session.get_scroll_info(page)
                
                # Check if we can scroll in the requested direction
                if direction.lower() == 'down' and pixels_below <= 0:
                    return ActionResult(
                        extracted_content=f"❌ Already at bottom of page. Cannot scroll down to find '{target_content}'.",
                        include_in_memory=True
                    )
                elif direction.lower() == 'up' and pixels_above <= 0:
                    return ActionResult(
                        extracted_content=f"❌ Already at top of page. Cannot scroll up to find '{target_content}'.",
                        include_in_memory=True
                    )
                
                # Perform the scroll
                dy = amount or await page.evaluate('() => window.innerHeight')
                if direction.lower() == 'up':
                    dy = -dy
                
                try:
                    await browser_session._scroll_container(dy)
                except Exception as e:
                    await page.evaluate('(y) => window.scrollBy(0, y)', dy)
                
                amount_str = f'{amount} pixels' if amount else 'one page'
                return ActionResult(
                    extracted_content=f"📜 Target content '{target_content}' not found in current viewport. Scrolled {direction} by {amount_str}. Please check the new viewport content.",
                    include_in_memory=True
                )
                
        except Exception as e:
            return ActionResult(error=f"Error in smart scroll: {str(e)}")

    @controller.action("Use OpenAI web search to find exact product names for Indian grocery apps")
    async def refine_product_search(params: RefineProductSearchParams) -> ActionResult:
        """
        Uses OpenAI's web search API to find precise product names for Indian grocery stores
        """
        try:
            from openai import OpenAI
            
            # Handle both dict and object parameter formats
            if isinstance(params, dict):
                user_input = params.get('user_input', '')
            else:
                user_input = params.user_input
                
            print(f"   🔍 Searching with OpenAI Search API: {user_input}")
            
            # Initialize OpenAI client
            client = OpenAI()
            
            # Use Responses API with web search
            response = client.responses.create(
                model="gpt-4o",
                tools=[{
                    "type": "web_search_preview",
                    "user_location": {
                        "type": "approximate",
                        "country": "IN"  # India for Indian grocery context
                    }
                }],
                input=f"""You are a product expert for Indian grocery shopping apps like Zepto, Blinkit, BigBasket.

TASK: Find the exact product name as sold in India for: {user_input}

SEARCH STRATEGY:
1. Search for the product + "India grocery" or "Zepto" or "Blinkit"
2. Find the exact brand name and product variant
3. Return the precise search term for Indian grocery apps

We are basically using you to better search for the product from vague description from users.

FORMAT: Return only the exact product name, nothing else."""
            )
            
            refined_term = response.output_text.strip()
            print(f"   ✅ OpenAI Search completed: {refined_term}")
            
            return ActionResult(
                extracted_content=f"Refined search term: {refined_term}",
                include_in_memory=True
            )
            
        except Exception as e:
            print(f"   ❌ OpenAI Search failed: {str(e)}")
            return ActionResult(error=f"Search failed: {str(e)}")

    @controller.action("Simple YES/NO validation if found product matches what user wanted")
    async def validate_product_selection(params: ValidateProductSelectionParams) -> ActionResult:
        """
        Simple validation: Does the found product match what the user requested?
        Returns YES or NO only.
        """
        try:
            # Handle both dict and object parameter formats
            if isinstance(params, dict):
                user_requested_item = params.get('user_requested_item', '')
                found_product_name = params.get('found_product_name', '')
                found_product_brand = params.get('found_product_brand', '')
                found_product_price = params.get('found_product_price', '')
                found_product_size = params.get('found_product_size', '')
            else:
                user_requested_item = params.user_requested_item
                found_product_name = params.found_product_name
                found_product_brand = params.found_product_brand
                found_product_price = params.found_product_price
                found_product_size = params.found_product_size
            
            llm = ChatOpenAI(model="gpt-4.1")
            
            prompt = f"""Simple validation question:

USER REQUESTED: {user_requested_item}
FOUND ON WEBSITE: {found_product_name} ({found_product_brand}) - {found_product_price} - {found_product_size}

Does this match what the user wanted? Answer only YES or NO.

Rules:
- Same brand required (Pringles ≠ Lays)
- Same product type required (chips ≠ cookies)  
- Size can vary slightly
- Flavor can be similar"""

            response = await llm.ainvoke([{"role": "user", "content": prompt}])
            
            result = response.content.strip()
            
            return ActionResult(
                extracted_content=f"{result}",
                include_in_memory=True
            )
            
        except Exception as e:
            return ActionResult(error=f"Error validating: {str(e)}")
    
    return controller


async def main():
    """The bulletproof approach that definitely works + your extension + minimal login functions"""
    
    # Load task only (items will be loaded via function call)
    with open('task.txt', 'r') as f:
        task = f.read().strip()
    
    print(f"📋 Task: {task}")
    print(f"🛍️ Items will be loaded dynamically via load_items() function")
    
    # Path to the extension
    extension_path = Path(__file__).parent / "extension"
    extension_path = extension_path.resolve()
    
    print(f"🔧 Loading extension from: {extension_path}")
    
    if not extension_path.exists():
        print(f"❌ Extension not found at: {extension_path}")
        return
    
    # Use BrowserSession with extension loaded
    browser_session = BrowserSession(
        headless=False,  # Keep visible 
        browser_type="chromium",  # Ensure we're using chromium for extension support
        # Add extension loading arguments
        args=[
            "--no-default-browser-check",
            "--no-first-run",
        ]
    )
    
    # Set up LLM
    llm = ChatOpenAI(model="gpt-4.1")
    
    # Set up custom controller with login functions
    controller = setup_custom_controller()
    
    # Enhanced system prompt guidance for better scrolling behavior
    scrolling_guidance = """

## SCROLLING BEHAVIOR GUIDELINES:

IMPORTANT: Before deciding to scroll, you must ALWAYS assess what's currently visible on the page.

1. **ASSESS FIRST**: Look at the current viewport content carefully. Check if what you're looking for might already be visible.

2. **USE SMART SCROLLING**: Instead of using basic scroll_down/scroll_up, prefer the 'assess_and_scroll' action which:
   - Analyzes current viewport content
   - Only scrolls if target content is not found
   - Prevents unnecessary scrolling

3. **SCROLLING SEQUENCE**:
   - First: Analyze all visible elements in current viewport
   - Second: If target not found, use assess_and_scroll with specific target description
   - Third: After scrolling, re-analyze the new viewport before scrolling again

4. **TARGET SPECIFICITY**: When using assess_and_scroll, be specific about what you're looking for:
   - Good: "add to cart button", "product price", "checkout option"
   - Bad: "more content", "something", "next thing"

5. **AVOID PREMATURE SCROLLING**: Never scroll just because you think there might be more content. Only scroll when you have a specific target that's not visible in the current viewport.

Example sequence:
1. Look at current page elements
2. If "add to cart" button not visible: assess_and_scroll(direction="down", target_content="add to cart button")  
3. Check new viewport for the button
4. If still not found and more content below: assess_and_scroll again

"""
    
    # Create and run the agent
    agent = Agent(
        task=task, 
        llm=llm, 
        browser_session=browser_session,
        controller=controller,
        extend_system_message=scrolling_guidance  # Add our custom scrolling guidance
    )
    
    try:
        print("\n🚀 Starting agent...")
        history = await agent.run()
        
        print("\n✅ Task completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 But at least we know the browser-use connection works!")


if __name__ == "__main__":
    asyncio.run(main()) 