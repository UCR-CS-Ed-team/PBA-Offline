#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;
   
   cin >> firstName;
   firstName = Eric;
   cin >> genericLocation;
   genericLocation = Chipotle;
   cin >> pluralNoun;
   pluralNoun = cars;
   cin >> wholeNumber;
   wholeNumber = 12;
   
   return 0;
}