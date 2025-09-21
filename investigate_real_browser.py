#!/usr/bin/env python3
"""
Investigate what's actually happening in a real browser session
"""

from playwright.sync_api import sync_playwright
import time

def investigate_real_browser():
    with sync_playwright() as p:
        # Use actual browser (not headless) to mimic your experience
        browser = p.chromium.launch(headless=False, slow_mo=1000)  # Slow down to see what happens
        page = browser.new_page()

        # Capture all console messages and errors
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f'[{msg.type.upper()}] {msg.text}'))

        # Capture JavaScript errors
        page.on('pageerror', lambda error: console_logs.append(f'[PAGE ERROR] {error}'))

        # Capture network failures
        page.on('requestfailed', lambda req: console_logs.append(f'[NETWORK FAIL] {req.url}: {req.failure}'))

        print('🌐 Opening CCOM Mobile UI...')
        response = page.goto('http://localhost:9002')
        print(f'📡 Initial response status: {response.status}')

        # Wait for the select element
        page.wait_for_selector('#project-select', timeout=10000)
        print('✅ Select element found')

        # Check initial dropdown content (before JS executes)
        initial_html = page.evaluate('''() => {
            const select = document.getElementById('project-select');
            return {
                innerHTML: select.innerHTML,
                optionCount: select.options.length,
                firstOptionText: select.options[0]?.text || 'NO OPTIONS'
            };
        }''')

        print(f'📄 Initial dropdown HTML: {initial_html}')

        # Wait and observe the dropdown evolution
        print('⏳ Waiting for JavaScript to load projects...')
        for i in range(10):  # Wait up to 10 seconds, checking every second
            time.sleep(1)
            current_state = page.evaluate('''() => {
                const select = document.getElementById('project-select');
                return {
                    optionCount: select.options.length,
                    options: Array.from(select.options).map(opt => opt.text),
                    projectsVariable: window.projects ? window.projects.length : 'undefined'
                };
            }''')

            print(f'⏱️  Second {i+1}: {current_state["optionCount"]} options: {current_state["options"]} | projects var: {current_state["projectsVariable"]}')

            # Stop if we see changes
            if current_state["optionCount"] > 1 or (current_state["optionCount"] == 1 and 'Loading' not in str(current_state["options"])):
                break

        # Check final state
        final_state = page.evaluate('''() => {
            const select = document.getElementById('project-select');
            return {
                innerHTML: select.innerHTML,
                optionCount: select.options.length,
                options: Array.from(select.options).map(opt => ({text: opt.text, value: opt.value})),
                selectedIndex: select.selectedIndex,
                projectsVar: window.projects,
                currentProjectPath: window.currentProjectPath
            };
        }''')

        print('\\n📋 FINAL STATE:')
        print(f'   Options count: {final_state["optionCount"]}')
        print(f'   Selected index: {final_state["selectedIndex"]}')
        print(f'   Projects variable: {final_state["projectsVar"]}')
        print(f'   Current path: {final_state["currentProjectPath"]}')

        for i, opt in enumerate(final_state["options"]):
            marker = " ← SELECTED" if i == final_state["selectedIndex"] else ""
            print(f'   {i+1}. "{opt["text"]}" = {opt["value"]}{marker}')

        # Show any console errors
        if console_logs:
            print('\\n🐛 CONSOLE LOGS/ERRORS:')
            for log in console_logs:
                print(f'   {log}')

        # Manual test - click the dropdown
        print('\\n🖱️  Clicking dropdown to see behavior...')
        page.click('#project-select')
        time.sleep(2)

        input('\\n⏸️  Press Enter to close browser...')
        browser.close()

if __name__ == '__main__':
    investigate_real_browser()