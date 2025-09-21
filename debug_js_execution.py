#!/usr/bin/env python3
"""
Debug the exact JavaScript execution that populates dropdown
"""

from playwright.sync_api import sync_playwright
import time

def debug_js_execution():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture JavaScript errors
        js_errors = []
        page.on('pageerror', lambda error: js_errors.append(str(error)))
        page.on('console', lambda msg: print(f'[CONSOLE {msg.type}] {msg.text}') if msg.type in ['error', 'warning'] else None)

        page.goto('http://localhost:9002')
        page.wait_for_selector('#project-select')
        time.sleep(3)

        # Test the exact JavaScript that should populate the dropdown
        debug_info = page.evaluate('''() => {
            // Simulate the loadProjects function step by step
            const steps = {};

            try {
                steps.step1_fetchCall = 'About to fetch /projects';

                // Check if we can access fetch
                steps.step2_fetchExists = typeof fetch !== 'undefined';

                // Check projects variable
                steps.step3_projectsVar = window.projects;

                // Check the actual select element
                const select = document.getElementById('project-select');
                steps.step4_selectExists = !!select;
                steps.step5_selectHTML = select ? select.innerHTML : 'NO SELECT';

                // Try to manually populate with test data
                if (select) {
                    const testProjects = [
                        {name: "test1", path: "/test1"},
                        {name: "test2", path: "/test2"}
                    ];

                    steps.step6_testData = testProjects;

                    try {
                        const testHTML = testProjects.map(p => `<option value="${p.path}">${p.name}</option>`).join('');
                        steps.step7_mapJoinResult = testHTML;

                        // Temporarily set it to see if the issue is in the assignment
                        select.innerHTML = testHTML;
                        steps.step8_afterAssignment = Array.from(select.options).map(opt => opt.text);

                        // Restore original
                        steps.step9_restoringOriginal = 'about to restore';

                    } catch (mapError) {
                        steps.step7_mapError = mapError.toString();
                    }
                }

            } catch (error) {
                steps.error = error.toString();
            }

            return steps;
        }''')

        print('🔍 JavaScript Execution Debug:')
        for key, value in debug_info.items():
            print(f'   {key}: {value}')

        # Check if there were any JS errors
        if js_errors:
            print('\\n🚨 JavaScript Errors:')
            for error in js_errors:
                print(f'   {error}')

        browser.close()

if __name__ == '__main__':
    debug_js_execution()