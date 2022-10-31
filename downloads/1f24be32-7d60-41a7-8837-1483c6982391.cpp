#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   firstName = "Eric" << endl;
   genericLocation = "Chipotle" << endl;
   wholeNumber = 12 << endl;
   pluralNoun = "cars";
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}