"""
UI Test: Verify Rotten Tomatoes scores and trailer links display on swipe cards.

This script:
1. Navigates to the app
2. Selects a user
3. Takes screenshots of the swipe screen
4. Checks for RT score and trailer link elements
"""
from playwright.sync_api import sync_playwright
import json

def test_swipe_screen_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 390, 'height': 844})  # iPhone 14 size

        print("1. Navigating to app...")
        page.goto('http://localhost:5173')
        page.wait_for_load_state('networkidle')

        # Take screenshot of user select screen
        page.screenshot(path='/tmp/01_user_select.png')
        print("   Screenshot: /tmp/01_user_select.png")

        # Find and click on first user
        print("2. Selecting first user...")
        page.wait_for_selector('.member-card, .user-card, button')

        # Get the page content to understand structure
        members = page.locator('.member-card').all()
        if not members:
            members = page.locator('button').all()

        if members:
            members[0].click()
            page.wait_for_load_state('networkidle')
            page.wait_for_timeout(1000)  # Wait for animations

        # Take screenshot of swipe screen
        page.screenshot(path='/tmp/02_swipe_screen.png')
        print("   Screenshot: /tmp/02_swipe_screen.png")

        # Check for movie card
        print("3. Checking for movie card elements...")
        movie_card = page.locator('.movie-card').first

        if movie_card.count() > 0:
            # Get the card's HTML to inspect
            card_html = movie_card.inner_html()

            # Check for RT score
            rt_score = page.locator('.rt-score, text=/🍅/')
            has_rt_score = rt_score.count() > 0
            print(f"   RT Score element found: {has_rt_score}")

            # Check for trailer link
            trailer_link = page.locator('.trailer-link, text=/Trailer/')
            has_trailer = trailer_link.count() > 0
            print(f"   Trailer link element found: {has_trailer}")

            # Check for meta section
            meta = page.locator('.movie-card .meta')
            if meta.count() > 0:
                meta_text = meta.inner_text()
                print(f"   Meta section content: {meta_text}")

            # Take close-up of card info
            info_section = page.locator('.movie-card .info').first
            if info_section.count() > 0:
                info_section.screenshot(path='/tmp/03_card_info.png')
                print("   Screenshot: /tmp/03_card_info.png")
        else:
            print("   No movie card found - may need to add movies first")

        # Check the DOM structure
        print("\n4. Inspecting page structure...")
        content = page.content()

        # Look for RT and trailer patterns in HTML
        has_rt_in_html = '🍅' in content or 'rt-score' in content or 'rt_critic' in content
        has_trailer_in_html = 'Trailer' in content or 'trailer-link' in content or 'youtube.com' in content

        print(f"   RT score pattern in HTML: {has_rt_in_html}")
        print(f"   Trailer pattern in HTML: {has_trailer_in_html}")

        # Navigate to watchlist to check movie data
        print("\n5. Checking watchlist for movie data...")
        page.goto('http://localhost:5173/watchlist')
        page.wait_for_load_state('networkidle')
        page.wait_for_timeout(500)

        page.screenshot(path='/tmp/04_watchlist.png')
        print("   Screenshot: /tmp/04_watchlist.png")

        browser.close()

        print("\n=== UI Test Complete ===")
        print("Screenshots saved to /tmp/")
        return has_rt_in_html or has_trailer_in_html

if __name__ == '__main__':
    result = test_swipe_screen_ui()
    print(f"\nResult: {'PASS' if result else 'NEEDS INVESTIGATION'}")
