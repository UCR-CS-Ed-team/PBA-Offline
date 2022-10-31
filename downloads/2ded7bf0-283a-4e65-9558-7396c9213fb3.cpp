#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   firstName = Eric;
   genericLocation = Chipotle;
   pluralNoun = cars;
   cin >> wholeNumber;
   wholeNumber = 12;
   
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}