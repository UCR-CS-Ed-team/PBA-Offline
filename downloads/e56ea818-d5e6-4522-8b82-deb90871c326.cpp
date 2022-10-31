#include <iostream>
using namespace std;

int main() {
   /* These are the variables. String is used for words/special characters. Int is used for whole numbers variables and fractions can't be input here. */
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* cin command can compound multiple variables (string and integer). */
   /* make sure to add space when predefining the variables (string and integer) */
   
   cin >> firstName >> genericLocation >> wholeNumber >> pluralNoun;
  
   
   /* This multi-statement is the structure of the output. the variables are inserted where they will need to be definied afterwords. */
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}