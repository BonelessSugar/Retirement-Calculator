import random
import csv
import math

# Federal taxes
# round because that's how they calculate it
def fedTax(income, i):
    stded = 13850 + i * 500
    ded10 = 11000 + i * 200
    ded12 = 44725 + i * 500
    ded22 = 93375 + i * 1000
    income -= stded
    if income <= 0:
        return 0
    if income <= ded10:
        return round(income * 0.10, 2)
    if income <= ded12:
        return round(ded10 * 0.10 + (income - ded10) * 0.12, 2)
    if income <= ded22:
        return round(ded10 * 0.10 + (ded12 - ded10) * 0.12 + (income - ded12) * 0.22, 2)
    return round(ded10 * 0.10 + (ded12 - ded10) * 0.12 + (ded22 - ded12) * 0.22 + (income - ded22) * 0.24, 2)

# Maine state taxes
def stateTax(income, i):
    stded = 13850 + i * 500
    ded58 = 24500 + i * 500
    ded675 = 58050 + i * 1000
    income -= stded
    if income <= 0:
        return 0
    if income <= ded58:
        return round(income * 0.058, 2)
    if income <= ded675:
        return round(ded58 * 0.058 + (income - ded58) * 0.0675, 2)
    return round(ded58 * 0.058 + (ded675 - ded58) * 0.0675 + (income - ded675) * 0.0715, 2)

# Social Security and Medicare tax
def SSMed(income):
    return round(income * 0.0765, 2)

# 401k can only go to 3 decimals after percent EX: 44.208%
# find the highest 401k contribution percent (round down) that is still above (expenses + rothIRA)
# by recursively calculating taxes of income after (401k + standard deduction)
# returns 0.44208
'''
trying to equal expenses + max roth IRA contribution (36,500)
income = 60,000
expenses = 30,000
max Roth IRA = 6,500
0%, income * (1 - 0.00) * taxes = 0, min = 0
75%, 60,000 * (1 - 0.75) - 1329.20 = 13,670 < 36,000, max = 0.75
37.5 = 30,641 < 36,000, max = 0.375
18.75 = 38,929, > 36,000 min = 0.1875
28.125 = 34,789, <, max
23.4375 = 36,859, >, min
etc.
'''
def find401k(income, rothIRA, expenses, i, rateMin=0.0, rateMax=0.75, prevTax=0):
    # this is the formula that does all the work
    curr401k = (rateMax - rateMin) * 0.5 + rateMin
    contribution401k = income * curr401k
    taxes = fedTax(income - contribution401k, i) + stateTax(income - contribution401k, i) + SSMed(income - contribution401k)
    if taxes == prevTax:
        # this is usually the final return statement
        # math.floor because I want to round down, otherwise I would use money I wouldn't have
        # 100,000 because 0.44208 * 100,000 = 44208
        return math.floor(curr401k * 100000) / 100000
    incomeAfterTaxAnd401k = (income - contribution401k) - taxes
    if incomeAfterTaxAnd401k > (expenses + rothIRA):
        return find401k(income, rothIRA, expenses, i, curr401k, rateMax, taxes)
    elif incomeAfterTaxAnd401k < (expenses + rothIRA):
        return find401k(income, rothIRA, expenses, i, rateMin, curr401k, taxes)
    return math.floor(curr401k * 100000) / 100000

# using CPIW data to calculate COLA for annual inflation rate
prevCPIW = 49.7 + 50.3 + 50.9
COLA = []
with open('CPI-W.csv', newline='') as csvfile:
    lineCount = 0
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        if lineCount > 1:
            for contents in row:
                filterContent = contents.split(",")
                currCPIW = float(filterContent[7]) + float(filterContent[8]) + float(filterContent[9])
                COLA.append((currCPIW / prevCPIW) - 1)
                prevCPIW = currCPIW
        lineCount += 1

# randomize monthly VTSAX returns
fundDiv = {}
with open('VTSAX dividend.csv', newline='') as csvfile:
    lineCount = 0
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        if lineCount != 0:
            for contents in row:
                filterContent = contents.split(",")
                filterContent[0] = filterContent[0].split("/")
                year = int(filterContent[0][2])
                month = int(filterContent[0][0])
                day = int(filterContent[0][1])
                price = float(filterContent[1])
                # {divYear: {divMonth: [divDay, $perShare]}}
                if year not in fundDiv:
                    fundDiv.update({year: {month: [day, price]}})
                if month not in fundDiv[year]:
                    fundDiv[year].update({month: [day, price]})
        lineCount += 1

# use avg dividend percent every 3mo
fundDivPercent = []
fundStock = {}
with open('VTSAX stock.csv', newline='') as csvfile:
    lineCount = 0
    spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in spamreader:
        if lineCount != 0:
            for contents in row:
                filterContent = contents.split(",")
                filterContent[0] = filterContent[0].split("/")
                year = int(filterContent[0][2])
                month = int(filterContent[0][0])
                day = int(filterContent[0][1])
                price = float(filterContent[1])
                if year not in fundStock:
                    fundStock.update({year: {month: price}})
                if month not in fundStock[year]:
                    fundStock[year].update({month: price})
                # {year: {month: start price}}
                # add div price
                if month in fundDiv[year]:
                    if day == fundDiv[year][month][0]:
                        # add div percent as function of current stock price
                        # fundDiv -- {divYear: {divMonth: [divDay, $perShare]}}
                        fundDivPercent.append(fundDiv[year][month][1] / price)
        lineCount += 1
avgDivAdditionalStockCount = sum(fundDivPercent)/len(fundDivPercent)

VTSAXreturns = []
VTSAXstart = fundStock[2000][12]
for year in fundStock:
    if year > 2000:
        for month in fundStock[year]:
            VTSAXreturns.append((fundStock[year][month] / VTSAXstart) - 1)
            VTSAXstart = fundStock[year][month]

'''
#find 70,000 expenses
income = 70000
multiplier = 1
#<70k
print(income * multiplier - (fedTax(income * multiplier,21) + stateTax(income * multiplier,21) + 0.10 * income * multiplier))
multiplier = 2
#>70k
#(2 - 1) * 0.5 + 1 = 1.5
multiplier = 1.5
#>70k
#(1.5 - 1) * 0.5 + 1 = 1.25
multiplier = 1.25
#<70k
#(1.5 - 1.25) * 0.5 + 1.25 = 1.375
multiplier = 1.375
#>70k
#(1.375 - 1.25) * 0.5 + 1.25 = 1.3125
multiplier = 1.3125
#<70k
'''
def findFundsBeforeTax(expenses, i, penalty, rateMin=1.0, rateMax=2.0, prevTax=0):
    rate = (rateMax - rateMin) * 0.5 + rateMin
    #expensesBeforeTaxes
    expB4Tax = expenses * rate
    #penalty = 10% before 59.5yo
    taxes = fedTax(expB4Tax, i) + stateTax(expB4Tax, i) + penalty * expB4Tax
    if round(taxes, 2) == round(prevTax, 2):
        #round up for expenses needed
        return math.ceil(expB4Tax * 100) / 100
    if (expB4Tax - taxes) > expenses:
        return findFundsBeforeTax(expenses, i, penalty, rateMin, rate, taxes)
    elif (expB4Tax - taxes) < expenses:
        return findFundsBeforeTax(expenses, i, penalty, rate, rateMax, taxes)
    return math.ceil(expB4Tax * 100) / 100

def isDollars(inputText):
    dollars = input(inputText)
    myLoop = True
    while myLoop:
        if "-" in dollars:
            dollars = input(inputText[:-2] + " cannot be negative. Please input zero or a positive number: ")
            continue
        if "," in dollars:
            dollars = dollars.replace(",", "")
        try:
            float(dollars)
        except:
            dollars = input("Please input a valid number for your " + inputText.lower())
            continue
        if "." in dollars:
            if dollars.index(".") + 3 < len(dollars):
                print("There may only be two digits past the decimal.")
                dollars = input("Please input a valid number for your " + inputText.lower())
                continue
        myLoop = False
    return float(dollars)

listStocks = []
listExpensesAtRetire = []
list401k = []
listBrokerage = []
listRoth = []
notEnoughMoneyCount = 0

defaultInput = input("Default input? (y/n): ")
while (defaultInput != 'y') and (defaultInput != 'n'):
    defaultInput = input("Default input? (y/n): ")
if defaultInput == 'y':
    currAge = 24
    retireAge = 45
    deathAge = 80
    incomeInput = 60000
    expensesInput = 30000
    trad401kInput = 28000
    rothIRAInput = 19000
    rothIRAPrincipalInput = 18000
    brokerageInput = 19000
    incomeSS = 4571
else:
    #current age
    currAge = input("Current age: ")
    while not currAge.isdigit():
        currAge = input("Please input a valid current age: ")
    currAge = int(currAge)
    #retirement age (before 59.5)
    retireAge = input("Retirement age (before 60): ")
    while (not retireAge.isdigit()) or (int(retireAge) < currAge) or (int(retireAge) >= 60):
        retireAge = input("Please input a valid retirement age: ")
    retireAge = int(retireAge)
    #death age
    deathAge = input("Death age: ")
    while (not deathAge.isdigit()) or (int(deathAge) < retireAge):
        deathAge = input("Please input a valid current age: ")
    deathAge = int(deathAge)
    #income
    incomeInput = isDollars("Income: ")
    #expenses
    expensesInput = isDollars("Expenses: ")
    while (expensesInput > incomeInput):
        print("Expenses cannot be higher than income.")
        expensesInput = isDollars("Expenses: ")
    #trad 401k
    trad401kInput = isDollars("Traditional 401k: ")
    #roth IRA
    rothIRAInput = isDollars("Roth IRA total: ")
    #roth IRA principal
    rothIRAPrincipalInput = isDollars("Roth IRA principal: ")
    #brokerage
    brokerageInput = isDollars("Brokerage: ")
    #Social Security at 62
    incomeSS = isDollars("Social security at age 62 in future dollars: ")

for k in range(0, 1000):
    rothPrincipal = rothIRAPrincipalInput
    income = incomeInput
    limitRothIRA = 6500
    limit401k = 22500
    expenses = expensesInput
    # round(5.599999999997,2) = 5.99999999997 for some reason
    total401k = trad401kInput
    totalRoth = rothIRAInput
    totalBrokerage = brokerageInput

    print("RUN: " + str(k+1))
    # regular calculation
    for i in range(0, retireAge - currAge):
        rothPrincipal += limitRothIRA
        totalRoth += limitRothIRA
        randomCOLA = 1 + random.choice(COLA)
        # print("RUN: " + str(i))
        add401k = find401k(income, limitRothIRA, expenses, i)
        for j in range(1, 13):
            if j % 3 == 0:
                totalRoth += (totalRoth * avgDivAdditionalStockCount)
                total401k += (total401k * avgDivAdditionalStockCount)
                totalBrokerage += (totalBrokerage * avgDivAdditionalStockCount)
            randomStockReturn = 1 + random.choice(VTSAXreturns)
            totalRoth *= randomStockReturn
            total401k *= randomStockReturn
            totalBrokerage *= randomStockReturn
            if (income * add401k) > limit401k:
                total401k += ((limit401k + (0.03 * income)) / 12)
                totalBrokerage += math.floor(((income * add401k) - limit401k) / 12 * 100) / 100
            else:
                total401k += ((income * (0.03 + add401k)) / 12)
        income *= randomCOLA
        expenses *= randomCOLA
        limit401k += 500
        if i != 0:
            if i % 4 == 0:
                limitRothIRA += 500
    listStocks.append(total401k + totalRoth + totalBrokerage)
    listBrokerage.append(totalBrokerage)
    list401k.append(total401k)
    listRoth.append(totalRoth)
    listExpensesAtRetire.append(expenses)
    # first withdraw Roth IRA principal or total Roth IRA, whichever is less
    # withdraw at end of month. So calc div, calc interest, then withdraw
    # just go with 10% penalty withdraw for 401k
    smallRoth = False
    if totalRoth < rothPrincipal:
        smallRoth = True
    passRoth = False
    if totalBrokerage > 0:
        passBrokerage = False
    else:
        passBrokerage = True
    pass401k = False
    for i in range((retireAge - currAge), (60 - currAge)):
        #print("${:,.2f}".format(expenses) + " / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))
        if total401k + totalRoth + totalBrokerage > 0:
            #print("{:.3%}".format(expenses / (total401k + totalRoth + totalBrokerage)))
            pass
        randomCOLA = 1 + random.choice(COLA)
        for j in range(1, 13):
            if j % 3 == 0:
                totalRoth += (totalRoth * avgDivAdditionalStockCount)
                total401k += (total401k * avgDivAdditionalStockCount)
                totalBrokerage += (totalBrokerage * avgDivAdditionalStockCount)
            randomStockReturn = 1 + random.choice(VTSAXreturns)
            totalRoth *= randomStockReturn
            total401k *= randomStockReturn
            totalBrokerage *= randomStockReturn
        #print("00000.00 / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))

        tempExpenses = expenses
        if not passRoth:
            if smallRoth:
                totalRoth -= tempExpenses
                tempExpenses = 0
                if totalRoth <= 0:
                    tempExpenses = -totalRoth
                    totalRoth = 0
                    passRoth = True
            else:
                #bug here, if totalRoth falls below rothPrincipal due to market forces, this won't update "correctly"
                rothPrincipal -= tempExpenses
                totalRoth -= tempExpenses
                tempExpenses = 0
                if rothPrincipal <= 0:
                    tempExpenses = -rothPrincipal
                    rothPrincipal = 0
                    passRoth = True
        if not passBrokerage:
            if tempExpenses > 0:
                totalBrokerage -= tempExpenses
                tempExpenses = 0
                if totalBrokerage <= 0:
                    tempExpenses = -totalBrokerage
                    totalBrokerage = 0
                    passBrokerage = True
        if not pass401k:
            if tempExpenses > 0:
                #find amount needed after fed, state, 10%
                needed401k = findFundsBeforeTax(tempExpenses, i, 0.10)
                total401k -= needed401k
                tempExpenses = 0
                if total401k <= 0:
                    tempExpenses = -total401k
                    total401k = 0
                    pass401k = True
                    if totalRoth <= 0:
                        print("NOT ENOUGH MONEY")
                        notEnoughMoneyCount += 1
        if totalRoth > 0:
            if tempExpenses > 0:
                #uhhh... do I pay capital gains on my 401k and roth IRA past principal?
                #I think no...
                #totalRoth gets penalized past principal, so 10% penalty
                totalRoth -= tempExpenses / 0.9
                if totalRoth <= 0:
                    totalRoth = 0
                    print("NOT ENOUGH MONEY")
                    notEnoughMoneyCount += 1
                    break

            #first take lesserRoth
            #then take brokerage
            #then take 401k
            #then take roth if left
            #make sure to set them to zero after fully withdrawn
        expenses *= randomCOLA
    # no more penalty
    for i in range((60 - currAge), (62 - currAge)):
        #print("${:,.2f}".format(expenses) + " / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))
        if total401k + totalRoth + totalBrokerage > 0:
            #print("{:.3%}".format(expenses / (total401k + totalRoth + totalBrokerage)))
            pass
        randomCOLA = 1 + random.choice(COLA)
        for j in range(1, 13):
            if j % 3 == 0:
                totalRoth += (totalRoth * avgDivAdditionalStockCount)
                total401k += (total401k * avgDivAdditionalStockCount)
                totalBrokerage += (totalBrokerage * avgDivAdditionalStockCount)
            randomStockReturn = 1 + random.choice(VTSAXreturns)
            totalRoth *= randomStockReturn
            total401k *= randomStockReturn
            totalBrokerage *= randomStockReturn
        #print("00000.00 / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))
        tempExpenses = expenses
        if not passRoth:
            if smallRoth:
                totalRoth -= tempExpenses
                tempExpenses = 0
                if totalRoth <= 0:
                    tempExpenses = -totalRoth
                    totalRoth = 0
                    passRoth = True
            else:
                # bug here, if totalRoth falls below rothPrincipal due to market forces, this won't update "correctly"
                rothPrincipal -= tempExpenses
                totalRoth -= tempExpenses
                tempExpenses = 0
                if rothPrincipal <= 0:
                    tempExpenses = -rothPrincipal
                    rothPrincipal = 0
                    passRoth = True
        if not passBrokerage:
            if tempExpenses > 0:
                totalBrokerage -= tempExpenses
                tempExpenses = 0
                if totalBrokerage <= 0:
                    tempExpenses = -totalBrokerage
                    totalBrokerage = 0
                    passBrokerage = True
        if not pass401k:
            if tempExpenses > 0:
                #here's where this changes to 0 instead of 10%, but still taxes
                needed401k = findFundsBeforeTax(tempExpenses, i, 0.0)
                total401k -= needed401k
                tempExpenses = 0
                if total401k <= 0:
                    tempExpenses = -total401k
                    total401k = 0
                    pass401k = True
                    if totalRoth <= 0:
                        print("NOT ENOUGH MONEY")
                        notEnoughMoneyCount += 1
        if totalRoth > 0:
            if tempExpenses > 0:
                totalRoth -= tempExpenses
                if totalRoth <= 0:
                    totalRoth = 0
                    print("NOT ENOUGH MONEY")
                    notEnoughMoneyCount += 1
                    break
        expenses *= randomCOLA
    # SS kicks in
    for i in range((62 - currAge), (deathAge - currAge)):
        #print("${:,.2f}".format(expenses) + " / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))
        if total401k + totalRoth + totalBrokerage > 0:
            #print("{:.3%}".format(expenses / (total401k + totalRoth + totalBrokerage)))
            pass
        # SS at 62: 4,571
        income = incomeSS
        randomCOLA = 1 + random.choice(COLA)
        for j in range(1, 13):
            if j % 3 == 0:
                totalRoth += (totalRoth * avgDivAdditionalStockCount)
                total401k += (total401k * avgDivAdditionalStockCount)
                totalBrokerage += (totalBrokerage * avgDivAdditionalStockCount)
            randomStockReturn = 1 + random.choice(VTSAXreturns)
            totalRoth *= randomStockReturn
            total401k *= randomStockReturn
            totalBrokerage *= randomStockReturn
        #print("00000.00 / " + "${:,.2f}".format(total401k + totalRoth + totalBrokerage))
        tempExpenses = expenses - (income * 12)
        if not passRoth:
            if smallRoth:
                totalRoth -= tempExpenses
                tempExpenses = 0
                if totalRoth <= 0:
                    tempExpenses = -totalRoth
                    totalRoth = 0
                    passRoth = True
            else:
                # bug here, if totalRoth falls below rothPrincipal due to market forces, this won't update "correctly"
                rothPrincipal -= tempExpenses
                totalRoth -= tempExpenses
                tempExpenses = 0
                if rothPrincipal <= 0:
                    tempExpenses = -rothPrincipal
                    rothPrincipal = 0
                    passRoth = True
        if not passBrokerage:
            if tempExpenses > 0:
                totalBrokerage -= tempExpenses
                tempExpenses = 0
                if totalBrokerage <= 0:
                    tempExpenses = -totalBrokerage
                    totalBrokerage = 0
                    passBrokerage = True
        if not pass401k:
            if tempExpenses > 0:
                needed401k = findFundsBeforeTax(tempExpenses, i, 0.0)
                total401k -= needed401k
                tempExpenses = 0
                if total401k <= 0:
                    tempExpenses = -total401k
                    total401k = 0
                    pass401k = True
                    if totalRoth <= 0:
                        print("NOT ENOUGH MONEY")
                        notEnoughMoneyCount += 1
        #found a bug: if there's no roth left after 401k, it won't say that there's not enough money
        if totalRoth > 0:
            if tempExpenses > 0:
                totalRoth -= tempExpenses
                if totalRoth <= 0:
                    totalRoth = 0
                    print("NOT ENOUGH MONEY")
                    notEnoughMoneyCount += 1
                    break
        income *= randomCOLA
        expenses *= randomCOLA

#I think this works like it should?
print("CASES SUCCEEDED: {:.1%}".format((1000 - notEnoughMoneyCount)/1000))
avgStock = sum(listStocks) / len(listStocks)
print("AVERAGE FUNDS AT RETIRE: ${:0,.2f}".format(avgStock))
avgExpenses = sum(listExpensesAtRetire) / len(listExpensesAtRetire)
print("AVERAGE EXPENSES AT RETIRE: ${:0,.2f}".format(avgExpenses))
print("AVERAGE PERCENT WITHDRAWAL AT RETIRE: {:.3%}".format(avgExpenses / avgStock))

#yeah so rich, broke, dead says it should last me 100% of the time, I'm getting 66% with defaults
