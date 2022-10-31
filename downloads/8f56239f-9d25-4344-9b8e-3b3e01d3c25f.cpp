#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* Type your code here. */
   cin >> firstName;
   cin >> genericLocation;
   cin >> wholeNumber;
   cin >> pluralNoun; 
   
   cout << firstName;
   cout << " went to ";
   cout << genericLocation;
   cout << " to buy ";
   cout << wholeNumber;
   cout << " different types of ";
   cout << pluralNoun;
   cout << "." << endl;

   return 0;
}