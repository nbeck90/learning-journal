Feature: AJAX edit function
    Implement an edit function that uses AJAX from the detail page
    and brings up the edit function

    Scenario: Bring up the edit function
        Given a posts entry detail with a title New Title
        When I click the edit button
        Then I am presented with an edit feature
