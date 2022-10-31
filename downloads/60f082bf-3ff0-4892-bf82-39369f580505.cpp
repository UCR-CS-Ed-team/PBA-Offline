#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* Type your code here. */
   cout << "Type a name" << endl;
   cin >> firstName; 
   
   cout << "Type a location" << endl;
   cin >> genericLocation;
   
   cout << "Type a number" << endl;
   cin >> wholeNumber;
   
   cout << "Type a plural noun" << endl;
   cin >> pluralNoun;
   
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}