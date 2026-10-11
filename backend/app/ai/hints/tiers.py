"""Hint tier templates: tiers 1-4 x mistake class x {en, hi, mr}. No code anywhere; tier 4 is gapped pseudocode.

Content is language-neutral in structure (class + tier + optional divergence), wording per language. HI/MR wording is
pending the bilingual reviewer pass [NEEDS VERIFICATION]. Technical words (loop, index, array, variable) stay in English.
"""
from __future__ import annotations

LANGS = ("en", "hi", "mr")
GENERAL = "general"

# class -> [tier1, tier2, tier3, tier4], each a (en, hi, mr) tuple
_T: dict[str, list[tuple[str, str, str]]] = {
    "off_by_one_bound": [
        ("Check the first and last positions your loop visits. Does it include each of them exactly once?",
         "अपने लूप (loop) की पहली और आखिरी position देखिए। क्या वह हर एक को ठीक एक बार शामिल करता है?",
         "तुमच्या लूप (loop) ची पहिली आणि शेवटची position तपासा. तो प्रत्येकाला अगदी एकदाच घेतो का?"),
        ("Take a tiny input of two or three items and write down the loop's start and stop values. Which position is skipped or visited one time too many?",
         "दो-तीन items का छोटा input लीजिए और लूप (loop) के start और stop मान लिख लीजिए। कौन-सी position छूट रही है या एक बार ज़्यादा आ रही है?",
         "दोन-तीन items चा लहान input घ्या आणि लूप (loop) चे start आणि stop मूल्य लिहा. कोणती position सुटते किंवा एकदा जास्त येते?"),
        ("The loop boundary (its start or its stop condition) is off by one. Compare how many times it runs with how many items there are.",
         "लूप (loop) की सीमा (start या stop condition) एक से चूक रही है। देखिए वह कितनी बार चलता है और items कितने हैं।",
         "लूप (loop) ची सीमा (start किंवा stop condition) एकाने चुकत आहे. तो किती वेळा चालतो आणि items किती आहेत ते तपासा."),
        ("Plan in words:\n1. Decide the first position to visit: ____.\n2. Decide the last position to visit: ____.\n3. Repeat the step for every position from first to last, including the last.\n4. Check the plan on an input of size 1 and size 2.",
         "शब्दों में योजना:\n1. पहली position तय कीजिए: ____।\n2. आखिरी position तय कीजिए: ____।\n3. पहली से आखिरी तक, आखिरी समेत, हर position पर यह step दोहराइए।\n4. योजना को size 1 और size 2 के input पर जाँचिए।",
         "शब्दांत योजना:\n1. पहिली position ठरवा: ____.\n2. शेवटची position ठरवा: ____.\n3. पहिलीपासून शेवटीपर्यंत, शेवटीसह, प्रत्येक position वर हा step पुन्हा करा.\n4. योजना size 1 आणि size 2 च्या input वर तपासा."),
    ],
    "missing_empty_case": [
        ("What should your code return when the input is empty? Does it reach that case without an error?",
         "input खाली हो तो आपका कोड क्या लौटाना चाहिए? क्या वह बिना error के उस स्थिति तक पहुँचता है?",
         "input रिकामा असेल तर तुमचा कोड काय परत द्यायला हवा? तो error शिवाय त्या स्थितीपर्यंत पोहोचतो का?"),
        ("Trace your code by hand on an empty input. Which line is the first to fail or return something unexpected?",
         "खाली input पर अपने कोड को हाथ से चलाकर देखिए। कौन-सी पहली line fail होती है या अनपेक्षित मान देती है?",
         "रिकाम्या input वर तुमचा कोड हाताने चालवून पाहा. कोणती पहिली line fail होते किंवा अनपेक्षित मूल्य देते?"),
        ("The empty input is not handled before the main logic runs. Add a check at the very start that decides the answer for it.",
         "मुख्य logic चलने से पहले खाली input को संभाला नहीं गया है। शुरुआत में ही एक जाँच जोड़िए जो उसका उत्तर तय करे।",
         "मुख्य logic चालण्यापूर्वी रिकामा input हाताळलेला नाही. अगदी सुरुवातीला एक तपासणी जोडा जी त्याचे उत्तर ठरवेल."),
        ("Plan in words:\n1. If the input has no items, return ____.\n2. Otherwise start with ____.\n3. Process each item and update ____.\n4. Return ____ at the end.",
         "शब्दों में योजना:\n1. अगर input में कोई item नहीं है, तो ____ लौटाइए।\n2. वरना ____ से शुरू कीजिए।\n3. हर item को देखकर ____ अपडेट कीजिए।\n4. अंत में ____ लौटाइए।",
         "शब्दांत योजना:\n1. input मध्ये एकही item नसेल तर ____ परत द्या.\n2. नाहीतर ____ पासून सुरू करा.\n3. प्रत्येक item पाहून ____ अपडेट करा.\n4. शेवटी ____ परत द्या."),
    ],
    "wrong_init": [
        ("Look at the value each variable starts with. Is it safe for every possible input, including negative numbers?",
         "देखिए हर variable किस मान से शुरू होता है। क्या वह हर input के लिए सही है, negative संख्याओं के लिए भी?",
         "प्रत्येक variable कोणत्या मूल्याने सुरू होतो ते पाहा. ते प्रत्येक input साठी योग्य आहे का, negative संख्यांसाठीही?"),
        ("Choose an input where the very first item should win. Does the starting value of your tracking variable let it win?",
         "ऐसा input चुनिए जिसमें सबसे पहला item जीतना चाहिए। क्या आपके variable का शुरुआती मान उसे जीतने देता है?",
         "असा input निवडा ज्यात पहिला item जिंकायला हवा. तुमच्या variable चे सुरुवातीचे मूल्य त्याला जिंकू देते का?"),
        ("A variable starts with a value that is wrong for some inputs, so the first comparison or update gives a wrong result. Choose a starting value that can never beat a real item.",
         "एक variable ऐसे मान से शुरू होता है जो कुछ input के लिए गलत है, इसलिए पहली तुलना या अपडेट गलत नतीजा देती है। ऐसा शुरुआती मान चुनिए जो किसी असली item को कभी न हराए।",
         "एक variable काही input साठी चुकीच्या मूल्याने सुरू होतो, म्हणून पहिली तुलना किंवा अपडेट चुकीचा निकाल देते. असे सुरुवातीचे मूल्य निवडा जे खऱ्या item ला कधीच हरवत नाही."),
        ("Plan in words:\n1. Start the tracking variable with ____ (it must never beat a real item).\n2. For each item, compare it with ____.\n3. Update the variable only when ____.\n4. Return ____.",
         "शब्दों में योजना:\n1. variable को ____ से शुरू कीजिए (वह किसी असली item को न हराए)।\n2. हर item की तुलना ____ से कीजिए।\n3. variable तभी अपडेट कीजिए जब ____।\n4. ____ लौटाइए।",
         "शब्दांत योजना:\n1. variable ला ____ ने सुरू करा (ते खऱ्या item ला हरवू नये).\n2. प्रत्येक item ची तुलना ____ शी करा.\n3. variable तेव्हाच अपडेट करा जेव्हा ____.\n4. ____ परत द्या."),
    ],
    "wrong_comparison": [
        ("Check each comparison: should it be strict (less than) or inclusive (less than or equal)? What happens when two values are equal?",
         "हर तुलना जाँचिए: क्या वह strict (से छोटा) होनी चाहिए या inclusive (छोटा या बराबर)? दो मान बराबर हों तो क्या होता है?",
         "प्रत्येक तुलना तपासा: ती strict (पेक्षा लहान) हवी की inclusive (लहान किंवा बरोबर)? दोन मूल्ये समान असतील तर काय होते?"),
        ("Try an input where two values are equal. Walk through the comparison and note which branch is taken.",
         "ऐसा input लीजिए जिसमें दो मान बराबर हों। तुलना को चलाकर देखिए और नोट कीजिए कि कौन-सी शाखा चलती है।",
         "असा input घ्या ज्यात दोन मूल्ये समान आहेत. तुलना चालवून पाहा आणि कोणती शाखा चालते ते नोंदवा."),
        ("A comparison uses the wrong strictness or direction for equal or repeated values. Decide what should happen on equality, then adjust that one condition.",
         "एक तुलना बराबर या दोहराए गए मानों के लिए गलत strictness या दिशा इस्तेमाल करती है। तय कीजिए कि बराबरी पर क्या होना चाहिए, फिर वही एक condition ठीक कीजिए।",
         "एक तुलना समान किंवा पुनरावृत्त मूल्यांसाठी चुकीची strictness किंवा दिशा वापरते. समानतेवर काय व्हायला हवे ते ठरवा, मग ती एकच condition दुरुस्त करा."),
        ("Plan in words:\n1. When the two values are equal, we should ____.\n2. When the first is smaller, we should ____.\n3. When the first is larger, we should ____.\n4. Check all three cases on an example.",
         "शब्दों में योजना:\n1. दोनों मान बराबर हों तो ____ करना है।\n2. पहला छोटा हो तो ____ करना है।\n3. पहला बड़ा हो तो ____ करना है।\n4. तीनों स्थितियाँ एक उदाहरण पर जाँचिए।",
         "शब्दांत योजना:\n1. दोन्ही मूल्ये समान असतील तर ____ करायचे.\n2. पहिले लहान असेल तर ____ करायचे.\n3. पहिले मोठे असेल तर ____ करायचे.\n4. तिन्ही स्थिती एका उदाहरणावर तपासा."),
    ],
    "accumulator_reset": [
        ("Which variables collect a running result? Are they set back to their starting value at the right moment?",
         "कौन-से variable चलता हुआ नतीजा जमा करते हैं? क्या उन्हें सही समय पर शुरुआती मान पर लौटाया जाता है?",
         "कोणते variable चालू निकाल साठवतात? त्यांना योग्य वेळी सुरुवातीच्या मूल्यावर परत आणले जाते का?"),
        ("Write down the running variable after each outer step. Does it carry over a value from the previous step when it should start fresh (or the opposite)?",
         "हर बाहरी step के बाद उस variable का मान लिख लीजिए। क्या पिछले step का मान आगे आ रहा है जबकि उसे नए सिरे से शुरू होना चाहिए (या उल्टा)?",
         "प्रत्येक बाह्य step नंतर त्या variable चे मूल्य लिहा. मागील step चे मूल्य पुढे येते का, जेव्हा ते नव्याने सुरू व्हायला हवे (किंवा उलट)?"),
        ("A running total or counter is reset too early, too late, or never. Decide at which point in the loop it must go back to its starting value.",
         "कोई कुल योग या counter बहुत जल्दी, बहुत देर से या कभी reset नहीं होता। तय कीजिए कि लूप (loop) में किस जगह उसे शुरुआती मान पर लौटना चाहिए।",
         "एखादा एकूण किंवा counter खूप लवकर, खूप उशिरा किंवा कधीच reset होत नाही. लूप (loop) मध्ये कोणत्या ठिकाणी तो सुरुवातीच्या मूल्यावर परत यायला हवा ते ठरवा."),
        ("Plan in words:\n1. Before the loops, set ____ to ____.\n2. At the start of each round, reset ____ only if ____.\n3. Add to ____ for every matching item.\n4. Return ____ after the loops end.",
         "शब्दों में योजना:\n1. लूप (loop) से पहले ____ को ____ पर सेट कीजिए।\n2. हर दौर की शुरुआत में ____ को तभी reset कीजिए जब ____।\n3. हर मेल खाते item पर ____ में जोड़िए।\n4. लूप (loop) खत्म होने पर ____ लौटाइए।",
         "शब्दांत योजना:\n1. लूप (loop) पूर्वी ____ ला ____ वर सेट करा.\n2. प्रत्येक फेरीच्या सुरुवातीला ____ फक्त ____ असेल तरच reset करा.\n3. प्रत्येक जुळणाऱ्या item साठी ____ मध्ये जोडा.\n4. लूप (loop) संपल्यावर ____ परत द्या."),
    ],
    "wrong_operator": [
        ("Re-read each arithmetic or logical operator in your code. Does each one say what you mean in plain words?",
         "अपने कोड का हर गणितीय या तार्किक operator दोबारा पढ़िए। क्या हर एक वही कहता है जो आप सादे शब्दों में चाहते हैं?",
         "तुमच्या कोडमधील प्रत्येक गणिती किंवा तार्किक operator पुन्हा वाचा. प्रत्येक तेच सांगतो का जे तुम्हाला साध्या शब्दांत हवे आहे?"),
        ("Pick one line that calculates a value and compute it by hand with real numbers. Compare with what you intended.",
         "एक line चुनिए जो कोई मान निकालती है और उसे असली संख्याओं से हाथ से निकालिए। अपने इरादे से मिलाइए।",
         "मूल्य काढणारी एक line निवडा आणि ती खऱ्या संख्यांनी हाताने काढा. तुमच्या हेतूशी जुळवा."),
        ("An operator (plus versus minus, and versus or, or the kind of division) does not match the intended rule. Say the rule in words, then check the operator against it.",
         "कोई operator (जोड़ बनाम घटाव, and बनाम or, या भाग का प्रकार) इरादे वाले नियम से मेल नहीं खाता। नियम शब्दों में कहिए, फिर operator को उससे मिलाइए।",
         "एखादा operator (बेरीज विरुद्ध वजाबाकी, and विरुद्ध or, किंवा भागाकाराचा प्रकार) हेतूच्या नियमाशी जुळत नाही. नियम शब्दांत सांगा, मग operator त्याच्याशी तपासा."),
        ("Plan in words:\n1. The new value equals ____ combined with ____.\n2. Name the operation that does exactly this: ____.\n3. Check it on one example by hand.\n4. Use the same operation everywhere this rule applies.",
         "शब्दों में योजना:\n1. नया मान ____ और ____ को मिलाकर बनता है।\n2. वह operation बताइए जो ठीक यही करता है: ____।\n3. उसे एक उदाहरण पर हाथ से जाँचिए।\n4. जहाँ भी यह नियम लागू हो वहाँ वही operation इस्तेमाल कीजिए।",
         "शब्दांत योजना:\n1. नवीन मूल्य ____ आणि ____ यांना एकत्र करून बनते.\n2. नेमके हेच करणारा operation सांगा: ____.\n3. तो एका उदाहरणावर हाताने तपासा.\n4. हा नियम जिथे लागू होतो तिथे तोच operation वापरा."),
    ],
    "missing_edge_single": [
        ("Trace your code by hand on an input with exactly one element. Does every step still make sense?",
         "सिर्फ़ एक item वाले input पर अपने कोड को हाथ से चलाइए। क्या हर step अब भी सही बैठता है?",
         "फक्त एक item असलेल्या input वर तुमचा कोड हाताने चालवा. प्रत्येक step अजूनही योग्य वाटतो का?"),
        ("With one item, which part of your loop runs and which neighbour or comparison item does it expect? Does that item exist?",
         "एक item के साथ आपके लूप (loop) का कौन-सा हिस्सा चलता है और वह किस पड़ोसी या तुलना वाले item की उम्मीद करता है? क्या वह मौजूद है?",
         "एका item सह तुमच्या लूप (loop) चा कोणता भाग चालतो आणि तो कोणत्या शेजारी किंवा तुलनेच्या item ची अपेक्षा करतो? तो अस्तित्वात आहे का?"),
        ("The code assumes at least two items (for example it reads a neighbour or compares a pair). Handle the single-item case directly, before the general logic.",
         "कोड मानकर चलता है कि कम से कम दो items हैं (जैसे पड़ोसी को पढ़ना या जोड़ी की तुलना)। सामान्य logic से पहले एक-item वाली स्थिति सीधे संभालिए।",
         "कोड गृहीत धरतो की किमान दोन items आहेत (उदा. शेजारी वाचणे किंवा जोडीची तुलना). सामान्य logic पूर्वी एका-item ची स्थिती थेट हाताळा."),
        ("Plan in words:\n1. If there is exactly one item, the answer is ____.\n2. Otherwise start from ____.\n3. Compare each item with ____.\n4. Return ____.",
         "शब्दों में योजना:\n1. अगर ठीक एक item है, तो उत्तर ____ है।\n2. वरना ____ से शुरू कीजिए।\n3. हर item की तुलना ____ से कीजिए।\n4. ____ लौटाइए।",
         "शब्दांत योजना:\n1. जर नेमका एक item असेल तर उत्तर ____ आहे.\n2. नाहीतर ____ पासून सुरू करा.\n3. प्रत्येक item ची तुलना ____ शी करा.\n4. ____ परत द्या."),
    ],
    "hardcoded_output": [
        ("Does your code compute its answer from the input, or does it return a fixed value for known examples?",
         "क्या आपका कोड input से उत्तर निकालता है, या ज्ञात उदाहरणों के लिए तय मान लौटाता है?",
         "तुमचा कोड input वरून उत्तर काढतो का, की ज्ञात उदाहरणांसाठी ठराविक मूल्य परत देतो?"),
        ("Change one example input slightly. Would your code still give the right answer? Which part depends on the input?",
         "किसी उदाहरण का input थोड़ा बदलिए। क्या आपका कोड तब भी सही उत्तर देगा? कौन-सा हिस्सा input पर निर्भर है?",
         "एखाद्या उदाहरणाचा input थोडा बदला. तुमचा कोड तरीही योग्य उत्तर देईल का? कोणता भाग input वर अवलंबून आहे?"),
        ("The answer looks fixed to the sample cases. Say in words the rule that turns any input into the output, then write that rule.",
         "उत्तर नमूना मामलों से बँधा दिखता है। शब्दों में वह नियम कहिए जो किसी भी input को output में बदलता है, फिर वही नियम लिखिए।",
         "उत्तर नमुना प्रकरणांशी बांधलेले दिसते. कोणत्याही input ला output मध्ये बदलणारा नियम शब्दांत सांगा, मग तोच नियम लिहा."),
        ("Plan in words:\n1. Describe in one sentence how the output depends on the input: ____.\n2. Name what you must read from the input: ____.\n3. Compute ____ from it step by step.\n4. Return the computed value, never a constant.",
         "शब्दों में योजना:\n1. एक वाक्य में बताइए कि output, input पर कैसे निर्भर है: ____।\n2. बताइए कि input से क्या पढ़ना है: ____।\n3. उससे ____ को step by step निकालिए।\n4. निकाला हुआ मान लौटाइए, कभी कोई स्थिर मान नहीं।",
         "शब्दांत योजना:\n1. output हा input वर कसा अवलंबून आहे ते एका वाक्यात सांगा: ____.\n2. input मधून काय वाचायचे ते सांगा: ____.\n3. त्यातून ____ step by step काढा.\n4. काढलेले मूल्य परत द्या, कधीही स्थिर मूल्य नाही."),
    ],
    GENERAL: [
        ("Pick the smallest input where the output looks wrong and trace each variable line by line.",
         "सबसे छोटा वह input चुनिए जिसमें output गलत दिखता है और हर variable को line दर line चलाकर देखिए।",
         "सर्वात लहान तो input निवडा ज्यात output चुकीचा दिसतो आणि प्रत्येक variable line by line तपासा."),
        ("Compare, step by step, the value you expect with the value your code has. Where do they first differ?",
         "step दर step अपेक्षित मान को अपने कोड के मान से मिलाइए। पहली बार वे कहाँ अलग होते हैं?",
         "step by step अपेक्षित मूल्याची तुमच्या कोडमधील मूल्याशी तुलना करा. ते पहिल्यांदा कुठे वेगळे होतात?"),
        ("The first difference between expected and actual behaviour is the place to inspect. Re-read that condition or update and ask what it assumes.",
         "अपेक्षित और असली व्यवहार का पहला अंतर ही जाँचने की जगह है। उस condition या अपडेट को दोबारा पढ़िए और सोचिए कि वह क्या मानकर चलता है।",
         "अपेक्षित आणि प्रत्यक्ष वर्तनातील पहिला फरक हेच तपासण्याचे ठिकाण आहे. ती condition किंवा अपडेट पुन्हा वाचा आणि ती काय गृहीत धरते ते विचारा."),
        ("Plan in words:\n1. Write what you keep track of: ____.\n2. Write when you update it: ____.\n3. Write what you return: ____.\n4. Check each step on the smallest failing input.",
         "शब्दों में योजना:\n1. लिखिए कि आप क्या ट्रैक करते हैं: ____।\n2. लिखिए कि उसे कब अपडेट करते हैं: ____।\n3. लिखिए कि क्या लौटाते हैं: ____।\n4. सबसे छोटे असफल input पर हर step जाँचिए।",
         "शब्दांत योजना:\n1. तुम्ही काय ट्रॅक करता ते लिहा: ____.\n2. ते केव्हा अपडेट करता ते लिहा: ____.\n3. तुम्ही काय परत देता ते लिहा: ____.\n4. सर्वात लहान अयशस्वी input वर प्रत्येक step तपासा."),
    ],
}

# failure class (engine) -> mistake class, used when the diagnoser gave no mistake class
_FROM_FAILURE = {"empty": "missing_empty_case", "single_element": "missing_edge_single", "boundary": "off_by_one_bound",
                 "duplicates": "wrong_comparison", "negatives": "wrong_init"}

_VAR = {"en": "Look at the variable `{v}`{where}. Work out by hand what it should hold after that step, then compare it with what your code computes.",
        "hi": "variable `{v}` को देखिए{where}। हाथ से निकालिए कि उस step के बाद उसमें क्या होना चाहिए, फिर अपने कोड के मान से मिलाइए।",
        "mr": "variable `{v}` पाहा{where}. त्या step नंतर त्यात काय असायला हवे ते हाताने काढा, मग तुमच्या कोडच्या मूल्याशी तुलना करा."}
_WHERE = {"en": " around iteration {i}", "hi": " (iteration {i} के आसपास)", "mr": " (iteration {i} च्या आसपास)"}
_LINE = {"en": "The behaviour first goes wrong near your line {n}.", "hi": "व्यवहार पहली बार आपकी line {n} के पास गलत होता है।",
         "mr": "वर्तन पहिल्यांदा तुमच्या line {n} जवळ चुकते."}


def norm_lang(lang: str | None) -> str:
    return lang if lang in LANGS else "en"


def resolve_class(mistake_class: str | None, failure_class: str | None = None) -> str:
    if mistake_class in _T:
        return mistake_class  # type: ignore[return-value]
    return _FROM_FAILURE.get(failure_class or "", GENERAL)


def template_hint(level: int, mistake_class: str | None = None, failure_class: str | None = None,
                  lang: str | None = "en", divergence: dict | None = None) -> str:
    """Deterministic, guard-safe hint text. Never raises for unknown inputs."""
    level = min(max(int(level or 1), 1), 4)
    lg = norm_lang(lang)
    idx = LANGS.index(lg)
    text = _T[resolve_class(mistake_class, failure_class)][level - 1][idx]
    div = divergence or {}
    if level == 2 and div.get("variable") and "`" not in text:
        where = _WHERE[lg].format(i=div["iteration"]) if div.get("iteration") else ""
        text = _VAR[lg].format(v=div["variable"], where=where) + " " + text
    elif level == 3 and div.get("line"):
        text = _LINE[lg].format(n=div["line"]) + " " + text
    return text


def mistake_classes() -> list[str]:
    return list(_T)
