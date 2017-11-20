def fizzbuzz(number):
	""" fizzbuzz(number) --> iterates a range from 1 to number (inclusive), printing:
		'FizzBuzz' if number is divisible by 3 and 5
		'Fizz' if number is divisible by 3
		'Buzz' if number is divisible by 5
		the number otherwise

		Prints an error if given anything but a positive
	"""
	if not isinstance(number, int) or number < 1:
		print "Only takes positive integers"
	else:
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