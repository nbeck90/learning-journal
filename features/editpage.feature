Feature: Post Editing
    Implement an edit functionality in our website that allows
    for changing the text/itle of a post while retaining the id.

    Scenario: Edit a post
        Given a posts detail page
        When I click the edit button
        Then I move to the edit page
