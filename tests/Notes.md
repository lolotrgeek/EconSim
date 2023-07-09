# Testing Notes

Run the system.

Does each of the componenets behave as it is supposed to?

## Low to High
test all types first
do their methods behave as expected?

## Agent Testing
1. mock the requester with a mock exchange agent -> requests -> 
2. 

## Exchange Testing
1. mock data
2. call each method
3. type check
4. is it actually giving us what we're asking for
5. i.e. we want midprice, mock the data so we know what the midprice is ahead of time, then run the method and see if it comes back with the same answer

question and answer methods
- get latest trade -> is biggest date in list?
- get_quotes -> 

### Order flow Testing
1. mock agent
2. call each order type
3. type check, ensure it gets put in trades
4. cancel -> place an order that cannot be filled
