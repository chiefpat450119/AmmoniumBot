from unittest import TestCase
from mistakes import MistakeChecker, mistakes, OfMistake, Mistake


class TestMistakeChecker(TestCase):
	def setUp(self):
		self.mistake_checker = MistakeChecker(mistakes)

	def test_find_mistake(self):
		self.assertEqual(self.mistake_checker.find_mistake("I should of done that").get_correction(), "should have")
		self.assertEqual(self.mistake_checker.find_mistake("I loose my mind").get_correction(), "lose")
		self.assertEqual(self.mistake_checker.find_mistake("I should of course do that"), None)
		self.assertEqual(self.mistake_checker.find_mistake("adskjflkjaslkdjflkjlsjdf"), None)
		self.assertEqual(self.mistake_checker.find_mistake("I should often"), None)
		self.assertEqual(self.mistake_checker.find_mistake("I could care less ").get_correction(), "couldn't care less")
		self.assertEqual(self.mistake_checker.find_mistake("I should of done that").get_explanation(),
		                 "Explanation: You probably meant to say could've/should've/would've which sounds like 'of' but is actually short for 'have'.")
		self.assertEqual(self.mistake_checker.find_mistake("I loose my mind").get_explanation(),
		                 "Explanation: Loose is an adjective meaning the opposite of tight, while lose is a verb.")
		self.assertEqual(self.mistake_checker.find_mistake("I should of course do that"), None)
		self.assertEqual(self.mistake_checker.find_mistake("adskjflkjaslkdjflkjlsjdf"), None)
		self.assertEqual(self.mistake_checker.find_mistake("I could care less ").get_explanation(),
		                 "Explanation: If you could care less, you do care, which is the opposite of what you meant to say.")
		self.assertIsNone(self.mistake_checker.find_mistake(""))


class TestMistake(TestCase):
	def setUp(self):
		self.mistake1 = OfMistake("shouldn't")
		self.mistake2 = Mistake("more then", "more than", exceptions=["any more", "some more"],
            explanation="If you didn't mean 'more than' you might have forgotten a comma.")


	def test_is_exception(self):
		self.assertTrue(self.mistake2.is_exception("If I don't like it any more then I will leave"))
		self.assertFalse(self.mistake2.is_exception("a lot more then that"))
		self.assertTrue(self.mistake1.is_exception("I shouldn't of course do that"))
		self.assertFalse(self.mistake1.is_exception("I shouldn't of done that"))

	def test_check(self):
		self.assertFalse(self.mistake1.check("I shouldn't of course do that"))
		self.assertTrue(self.mistake1.check("I shouldn't of done that"))
		self.assertFalse(self.mistake1.check(""))
		self.assertFalse(self.mistake1.check("aslkdjfljsajdljf"))
		self.assertFalse(self.mistake2.check("If I don't like it any more then I will leave"))
		self.assertTrue(self.mistake2.check("a lot more then that"))
		self.assertFalse(self.mistake2.check(""))
		self.assertFalse(self.mistake2.check("aslkdjfljsajdljf"))

	def test_find_context(self):
		self.assertEqual(self.mistake1.find_context("I shouldn't of done that"), "I shouldn't of done")
		self.assertEqual(self.mistake1.find_context("I shouldn't of course do that"), "I shouldn't of course")
		self.assertEqual(self.mistake2.find_context("If I don't like it any more then I will leave"), " any more then I")
		self.assertEqual(self.mistake2.find_context("a lot more then that"), " lot more then that")
		self.assertEqual(self.mistake1.find_context("I shouldn't of done that"), "I shouldn't of done")
		self.assertEqual(self.mistake1.find_context("I shouldn't of course do that"), "I shouldn't of course")
		self.assertEqual(self.mistake2.find_context("If I don't like it any more then I will leave"), " any more then I")
		self.assertEqual(self.mistake2.find_context("a lot more then that"), " lot more then that")

	def test_get_correction(self):
		self.assertEqual(self.mistake1.get_correction(), "shouldn't have")
		self.assertEqual(self.mistake2.get_correction(), "more than")

	def test_get_explanation(self):
		self.assertEqual(self.mistake1.get_explanation(), "Explanation: You probably meant to say could've/should've/would've which sounds like 'of' but is actually short for 'have'.")
		self.assertEqual(self.mistake2.get_explanation(), "Explanation: If you didn't mean 'more than' you might have forgotten a comma.")
