#include <iostream>
#include <string>

using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   firstName = Eric;
   genericLocation = Chipotle;
   wholeNumber = 12;
   pluralNoun = cars;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}