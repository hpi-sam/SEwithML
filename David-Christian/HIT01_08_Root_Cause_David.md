# Failure Description HIT01_08

## Failure

Failure description:

```java
java.lang.IllegalArgumentException: Minutes out of range: -15
```

Test description:
```java
assertEquals(DateTimeZone.forID("-02:15"), DateTimeZone.forOffsetHoursMinutes(-2, -15));
```

## Failure Explanation

The specification states, that the method accepts a minutes offset value in the range of -59 to 59 inlcusive. The method checks if this value is within these bounds on line 279, but incorrectly throws a "Minutes out of range" exception for any minutes offset less than zero instead of less than -59.