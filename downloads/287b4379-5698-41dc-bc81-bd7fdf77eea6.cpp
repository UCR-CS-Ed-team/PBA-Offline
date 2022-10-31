#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   cin >> firstName;
   cout << "Type in first name." << endl;
  
   cin >> genericLocation;
   cout << "Type in a generic location." << endl;
   
   cin >> wholeNumber;
   cout << "Type in a whole number." << endl; 
   
   cin >> pluralNoun;
   cout << "Type in a plural noun." << endl; 
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}