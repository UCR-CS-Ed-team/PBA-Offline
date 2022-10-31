#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cin >> firstName;
   firstName = Eric;
   cin >> genericLocation;
   genericLocation = Chipotle;
   cin >> pluralNoun;
   pluralNoun = cars;
   cin >> wholeNumber;
   wholeNumber = 12;
   
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}