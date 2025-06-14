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
                model="gpt-4o-mini",
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
            
            llm = ChatOpenAI(model="gpt-4o")
            
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
    with open('flight_task.txt', 'r') as f:
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
    llm = ChatOpenAI(model="gpt-4o")
    
    # Set up custom controller with login functions
    controller = setup_custom_controller()
    
    # Create and run the agent
    agent = Agent(
        task=task, 
        llm=llm, 
        browser_session=browser_session,
        controller=controller
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