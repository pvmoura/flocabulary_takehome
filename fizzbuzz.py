def fizzbuzz(number):
	for n in xrange(1, number + 1):
		if n % 3 == 0 and n % 5 == 0:
			print 'FizzBuzz'
		elif n % 3 == 0:
			print 'Fizz'
		elif n % 5 == 0:
			print 'Buzz'
		else:
			print n

if __name__ == '__main__':
	fizzbuzz(100)