#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   /* Type your code here. */
   cin >> firstName >> endl;
   cin >> genericLocation >> endl;
   cin >> wholeNumber >> endl;
   cin >> pluralNoun >> endl;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}