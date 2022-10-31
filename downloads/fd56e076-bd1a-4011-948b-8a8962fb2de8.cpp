#include <iostream>
using namespace std;

int main() {
   string firstName; 
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
 cin >> firstName;
 cout << " went to ";
 cin >> genericLocation;
 cout << " to buy ";
 cin >> wholeNumber;
 cout << " different types of";
 cin >> pluralNoun;
 cout << ".";
 cout << endl;
   
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}