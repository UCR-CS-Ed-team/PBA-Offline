#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* Type your code here. */
   // I created cin statements for the four above string and int statements.
   cin >> firstName;
   cin >> genericLocation;
   cin >> wholeNumber;
   cin >> pluralNoun;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}