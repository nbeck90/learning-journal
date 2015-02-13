Feature: Click a post to bring up a detail page for it
    Implement functionality such that when I click a post body
    or title, I am taken to a page that displays that post individually

    Scenario: A visitor selecting a post from home
        Given I am at the homepage
        When I select a posts title or body
        Then I am taken to a page with just the post I selected
