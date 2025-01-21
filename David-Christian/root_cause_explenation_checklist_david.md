# Checklist for good (root cause) explanations

- inlcude line number or range of lines where the root cause of the failure lies
- inlcude some (minimal) context what kind of failure the root cause is
    - e.g. wrong calculation, wrong implementation, ...
    - not just very specific to the single value in the test
- generally more abstract/high level description of issue
- name relevant variable/function names
    - with direct impact on the failure
    - required for context/understanding of explanation
    - name specific errors being thrown
- short and precise language
    - no redundant information
    - avoid vague wording
- reference to documentation or specification if relevant and available
    - short and specific
- explanation should be self-explanatory
    - i.e. able to understand the gist without additional resources
- correctness and understandability
