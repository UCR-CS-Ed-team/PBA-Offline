#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   firstName= "Eric";
   genericLocation = "Chipotle";
   wholeNumber = 12,
   pluralNoun = "cars";
   
   firstName= "Tiffany";
   genericLocation = "Disneyland";
   wholeNumber = 3,
   pluralNoun = "radios";
   
   firstName= "Scotty";
   genericLocation = "Ireland";
   wholeNumber = 154,
   pluralNoun = "oranges";
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}