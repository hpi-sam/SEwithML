## HIT01_08

#### Describing the root cause for the exception based on the explanations from the dataset.

The root cause for the thrown exception is in line 279. Within the if statement the program checks is the value of the variable "minutesOffset" is less than zero or greater than 59. The documentation states, that the value of the variable can also be negative in some cases. In a case with a negative "minutesOffset" value, the program throws the relevant exception. 

#### Checklist
- state the line or the function where the root cause is
- don't use specific numbers from the given exception (like minutesOffset was -15)
- ...