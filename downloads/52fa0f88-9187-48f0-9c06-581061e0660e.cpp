#include <iostream>
using namespace std;

int main() {
   string firstName;
   string genericLocation;
   int wholeNumber;
   string pluralNoun;
   
   scanner scnr = new scanner (system.in) ;

   string firstname;

   string genericlocation;

   int wholenumber;

   string pluralNoun;

   firstName = scnr.next();

   genericLocation = scnr.next();

   wholeNumner = scnr.nextInt();

   pluralNoun = scnr.nextLine();
   cout << firstName << " went to " << genericLocation << " to buy " << wholeNumber << " different types of " << pluralNoun << "." << endl;

   return 0;
}