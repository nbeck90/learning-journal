Feature: Post Edit Page
    Implement an edit page that can be accessed from the detail
    page if logged in.

    Scenario: Move to the edit page
        Given a posts detail page and I am logged in
        When I click the edit button
        Then I move to the edit page
