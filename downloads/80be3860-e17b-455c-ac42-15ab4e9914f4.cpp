#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* Type your code here. */
   firstName = input();
   genericLocation = input();
   wholeNumber = 12;
   pluralNoun = input();
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}