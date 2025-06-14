# Browser-Use Agent Setup

An AI agent that autonomously interacts with grocery shopping websites using browser-use and OpenAI. This agent can log in, search for products, and complete shopping tasks with minimal manual intervention.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- A modern browser (Chrome/Chromium recommended)

### 1. Install UV (Fast Python Package Manager)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### 2. Clone and Setup

```bash
git clone <your-repo-url>
cd gtm-agent

# Create virtual environment with Python 3.11
uv venv --python 3.11

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv sync
```

### 3. Install Browser-Use

```bash
# Install browser-use and required dependencies
uv add browser-use langchain-openai openai
```

### 4. Install Playwright Browser

```bash
# Install playwright browsers
playwright install chromium
```

### 5. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

Or export directly:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 6. Create Required Configuration Files

Create these files in the `gtm-agent` directory:

#### `task.txt`
```
Complete grocery shopping by adding items from the shopping list to cart and proceeding to checkout. Use the login details provided to authenticate.
```

#### `items.txt`
```
Pringles Original Flavor Chips
Coca Cola 1.25L
Bread - White/Brown
Milk - 1L Toned
Bananas - 1 dozen
```

#### `details.txt`
```
# Login Details for Grocery App
Phone: +91XXXXXXXXXX
Email: your.email@example.com
Password: your_password_here

# Tips:
# - For OTP, the agent will pause and wait for manual input
# - Make sure you have access to the phone number for OTP verification
# - The agent will handle most of the navigation automatically
```



### 7. Run the Agent

```bash
python working_browser.py
```

## 🎯 What the Agent Does

1. **Loads Configuration**: Reads task, items, and login details from respective files
2. **Opens Browser**: Launches Chromium with your extension loaded
3. **Navigates to Site**: Goes to the grocery shopping website
4. **Handles Authentication**: Uses provided credentials, pauses for OTP/manual steps
5. **Product Search**: Uses AI-powered search to find exact products
6. **Smart Shopping**: Validates products match your requirements
7. **Checkout Process**: Adds items to cart and proceeds to checkout

## 🔧 Features

### Custom Actions Available

- **`load_login_details()`**: Loads authentication info from `details.txt`
- **`wait_for_user()`**: Pauses for manual OTP/password input
- **`load_items()`**: Loads shopping list from `items.txt`
- **`assess_and_scroll()`**: Smart scrolling that only scrolls when needed
- **`refine_product_search()`**: Uses OpenAI web search for precise product matching
- **`validate_product_selection()`**: Confirms found products match requirements

### Smart Scrolling System

The agent includes an enhanced scrolling system that:
- Analyzes current viewport content before scrolling
- Only scrolls when target content is not visible
- Prevents unnecessary scrolling that can confuse the agent
- Uses OpenAI to assess if content is present

## 🛠️ Troubleshooting

### Common Issues

1. **Browser doesn't open**: 
   ```bash
   playwright install chromium
   ```

2. **OpenAI API errors**: 
   - Check your API key is valid
   - Ensure you have sufficient credits

3. **Extension not loading**: 
   - Verify extension files are in `extension/` directory
   - Check browser console for extension errors

4. **Agent gets stuck**: 
   - The agent will pause and wait for manual input during OTP/authentication
   - Press Enter after completing manual actions

### Debug Mode

To enable detailed logging, modify the script:

```python
# In working_browser.py, change headless to False and add debug
browser_session = BrowserSession(
    headless=False,  # Keep browser visible
    debug=True       # Enable debug logging
)
```

## 📝 Customization

### Adding New Shopping Sites

Modify the task in `task.txt` to target different grocery sites:

```
Navigate to BigBasket.com and complete grocery shopping...
```

### Custom Product Search

The agent uses OpenAI's web search API to find exact product names. It's optimized for Indian grocery stores but can be adapted:

```python
# In refine_product_search function
"user_location": {
    "type": "approximate", 
    "country": "US"  # Change country code
}
```

### Adding New Actions

```python
@controller.action("Your custom action description")
async def your_custom_action(params: YourParamsModel) -> ActionResult:
    # Your logic here
    return ActionResult(extracted_content="Success", include_in_memory=True)
```

## 🔐 Security Notes

- Never commit `details.txt` with real credentials
- Use environment variables for sensitive data
- The agent will pause for OTP input - never share OTP codes
- Review the agent's actions before confirming purchases

## 📋 Dependencies

- `browser-use`: Web automation framework
- `langchain-openai`: OpenAI integration
- `playwright`: Browser automation
- `pydantic`: Data validation
- `openai`: OpenAI API client

## 🤝 Contributing

1. Follow the browser-use coding guidelines
2. Use `uv` instead of `pip` for dependencies
3. Add type hints and Pydantic models for new actions
4. Test with real grocery sites before committing

## 📄 License

[Add your license here]

---

**Note**: This agent is designed for educational and personal use. Always respect website terms of service and rate limits when using automated tools. 